from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QFileDialog, 
    QMessageBox, QInputDialog, QComboBox, QLabel, QFormLayout, 
    QDialogButtonBox, QLineEdit, QTabWidget, QWidget
)
from PyQt5.QtGui import QIcon
from qgis.core import QgsProject, QgsRelation
import json
import uuid
from datetime import datetime

class RelazioniPluginDialog(QDialog):
    def __init__(self):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Relationship Manager")

        # Set plugin icon
        self.setWindowIcon(QIcon(':/plugins/relazioniplugin/icon.png'))

        # Create layout and widgets manually
        layout = QVBoxLayout()

        # Relationships list
        self.listaRelazioni = QListWidget()
        layout.addWidget(self.listaRelazioni)

        # Buttons with icons
        self.btnEsporta = QPushButton(QIcon(':/plugins/relazioniplugin/export.png'), "Export Relationships")
        layout.addWidget(self.btnEsporta)

        self.btnCarica = QPushButton(QIcon(':/plugins/relazioniplugin/import.png'), "Load Relationships")
        layout.addWidget(self.btnCarica)

        self.btnModifica = QPushButton(QIcon(':/plugins/relazioniplugin/edit.png'), "Edit Relationship")
        layout.addWidget(self.btnModifica)

        self.btnDuplica = QPushButton(QIcon(':/plugins/relazioniplugin/duplicate.png'), "Duplicate Relationship")
        layout.addWidget(self.btnDuplica)

        self.btnElimina = QPushButton(QIcon(':/plugins/relazioniplugin/delete.png'), "Delete Relationship")
        layout.addWidget(self.btnElimina)

        self.btnCrea = QPushButton(QIcon(':/plugins/relazioniplugin/create.png'), "Create Relationship")
        layout.addWidget(self.btnCrea)

        self.btnStorico = QPushButton(QIcon(':/plugins/relazioniplugin/history.png'), "View History")
        layout.addWidget(self.btnStorico)

        self.setLayout(layout)

        # Connect buttons to their functions
        self.btnEsporta.clicked.connect(self.esporta_relazioni)
        self.btnCarica.clicked.connect(self.carica_relazioni)
        self.btnModifica.clicked.connect(self.apri_modifica_relazione)
        self.btnDuplica.clicked.connect(self.duplica_relazione)
        self.btnElimina.clicked.connect(self.elimina_relazione)
        self.btnCrea.clicked.connect(self.crea_nuova_relazione)
        self.btnStorico.clicked.connect(self.visualizza_storico)

        # Load relationships on startup
        self.carica_lista_relazioni()

        # Initialize history storage
        self.history = []

    def carica_lista_relazioni(self):
        """List all relationships in the QGIS project."""
        self.listaRelazioni.clear()
        project = QgsProject.instance()

        # Get the relation manager
        relation_manager = project.relationManager()

        # Iterate through all relations and add to the list
        for relation in relation_manager.relations().values():
            self.listaRelazioni.addItem(f'{relation.id()}: {relation.name()}')

    def esporta_relazioni(self):
        """Export relationships to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export relationships", "", "JSON Files (*.json)")
        if file_path:
            relazioni = self.ottieni_relazioni()
            with open(file_path, 'w') as file:
                json.dump(relazioni, file, indent=4)
            QMessageBox.information(self, "Export", "Relationships exported successfully!")

    def carica_relazioni(self):
        """Load relationships from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load relationships", "", "JSON Files (*.json)")
        if not file_path:
            return  # Esci se l'utente annulla il file dialog

        with open(file_path, 'r') as file:
            try:
                relazioni = json.load(file)
                if not relazioni:
                    QMessageBox.warning(self, "Load Error", "The file is empty or invalid.")
                    return
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Load Error", "The file format is invalid. Please check the JSON file.")
                return

        project = QgsProject.instance()
        relation_manager = project.relationManager()

        # Variabili per tracciare lo stato
        relazioni_fallite = []
        relazioni_caricate = []

        for relazione_id, relazione in relazioni.items():
            if not relazione_id:
                relazioni_fallite.append(f"Invalid ID for relationship '{relazione['nome']}'")
                continue

            # Verifica se i layer esistono nel progetto
            layers_figlio = project.mapLayersByName(relazione['referencing_layer'])
            layers_padre = project.mapLayersByName(relazione['referenced_layer'])

            if not layers_figlio or not layers_padre:
                relazioni_fallite.append(f"Layer not found for relationship '{relazione['nome']}' (Parent: {relazione['referenced_layer']}, Child: {relazione['referencing_layer']})")
                continue

            layer_figlio = layers_figlio[0]
            layer_padre = layers_padre[0]

            # Crea una nuova relazione
            relation = QgsRelation()
            relation.setName(relazione['nome'])
            relation.setId(relazione_id)  # Usa l'ID dalla struttura JSON
            relation.setReferencingLayer(layer_figlio.id())
            relation.setReferencedLayer(layer_padre.id())

            # Aggiungi le coppie di chiavi
            valid_keys = True
            for chiave_padre, chiave_figlio in relazione['chiavi'].items():
                if chiave_padre in layer_padre.fields().names() and chiave_figlio in layer_figlio.fields().names():
                    relation.addFieldPair(chiave_padre, chiave_figlio)
                else:
                    relazioni_fallite.append(f"Invalid key pair: {chiave_padre} -> {chiave_figlio} in relationship '{relazione['nome']}'")
                    valid_keys = False
                    break

            # Aggiungi la relazione al manager se le chiavi sono valide
            if valid_keys:
                if relation_manager.addRelation(relation) or relation_manager.relation(relazione_id):
                    # La relazione è stata aggiunta o esiste già, considerala come caricata
                    relazioni_caricate.append(relazione['nome'])
                else:
                    relazioni_fallite.append(f"Failed to add relationship '{relazione['nome']}' to the project")

        # Mostra i risultati all'utente
        if relazioni_fallite:
            QMessageBox.warning(self, "Load Errors", f"Some relationships failed to load:\n" + "\n".join(relazioni_fallite))
        if relazioni_caricate:
            QMessageBox.information(self, "Load Success", f"Relationships loaded successfully:\n" + "\n".join(relazioni_caricate))

        # Aggiorna la lista delle relazioni se alcune sono state caricate
        if relazioni_caricate:
            self.carica_lista_relazioni()


    def apri_modifica_relazione(self):
        """Open the dialog to edit the selected relationship."""
        selected = self.listaRelazioni.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a relationship to edit.")
            return

        relazione_id = selected.text().split(":")[0]

        # Get the selected relation data
        relation = QgsProject.instance().relationManager().relation(relazione_id)
        if not relation:
            QMessageBox.warning(self, "Error", "Relationship not found.")
            return

        # Retrieve relation details
        relazione_details = self.ottieni_dettagli_relazione(relation)

        # Open the dialog to modify the relationship
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Relationship: {relazione_details['id']}")  # Mostra l'ID nella finestra
        layout = QFormLayout()

        # Pre-fill data
        nome_relazione = QLineEdit(relazione_details['nome'])
        layer_padre = self._crea_layer_combo(relazione_details['layer_padre'])
        layer_figlio = self._crea_layer_combo(relazione_details['layer_figlio'])  # Verifica layer figlio

        chiavi_padre = self._crea_field_combo(layer_padre.currentText(), list(relazione_details['chiavi'].keys())[0])
        chiavi_figlio = self._crea_field_combo(layer_figlio.currentText(), list(relazione_details['chiavi'].values())[0])

        layout.addRow("Relationship Name:", nome_relazione)
        layout.addRow("Parent Layer:", layer_padre)
        layout.addRow("Child Layer:", layer_figlio)
        layout.addRow("Parent Key:", chiavi_padre)
        layout.addRow("Child Key:", chiavi_figlio)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        # Connect the confirm button
        buttonBox.accepted.connect(lambda: self.modifica_relazione_esistente(relazione_details['id'], {
            'nome': nome_relazione.text(),
            'layer_padre': layer_padre.currentText(),
            'layer_figlio': layer_figlio.currentText(),
            'chiavi': {chiavi_padre.currentText(): chiavi_figlio.currentText()}
        }))
        buttonBox.rejected.connect(dialog.reject)

        dialog.exec()


    def duplica_relazione(self):
        """Duplicate the selected relationship."""
        selected = self.listaRelazioni.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a relationship to duplicate.")
            return

        relazione_id = selected.text().split(":")[0]
        project = QgsProject.instance()
        relation = project.relationManager().relation(relazione_id)

        # Verifica se il layer padre e figlio esistono
        layer_figlio = project.mapLayersByName(relation.referencingLayer().name())
        layer_padre = project.mapLayersByName(relation.referencedLayer().name())

        if not layer_figlio or not layer_padre:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return

        nuovo_nome, ok = QInputDialog.getText(self, "Duplicate Relationship", "Enter new relationship name:")
        if not ok or not nuovo_nome:
            return

        # Crea un nuovo ID per la relazione duplicata
        nuovo_id = f'duplicated_{relazione_id}_{str(uuid.uuid4())}'

        # Duplicare la relazione
        nuova_relazione = {
            'id': nuovo_id,
            'nome': nuovo_nome,
            'layer_figlio': layer_figlio[0].name(),
            'layer_padre': layer_padre[0].name(),
            'chiavi': relation.fieldPairs()
        }

        # Aggiungere la nuova relazione al progetto
        self.crea_relazione_esistente(nuova_relazione)  # Rimuove il controllo condizionale
        
        # Aggiungere l'azione alla cronologia
        self.add_to_history(f"Duplicated relationship: {nuovo_nome}", nuova_relazione)
        
        QMessageBox.information(self, "Duplicate", "Relationship duplicated successfully!")

        # Aggiornare la lista delle relazioni
        self.carica_lista_relazioni()

    def elimina_relazione(self):
        """Delete the selected relationship."""
        selected = self.listaRelazioni.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a relationship to delete.")
            return

        relazione_id = selected.text().split(":")[0]
        project = QgsProject.instance()
        relation_manager = project.relationManager()

        relation = relation_manager.relation(relazione_id)
        if not relation:
            QMessageBox.warning(self, "Error", "Relationship not found.")
            return

        # Save current state to history before deletion
        relazione_details = self.ottieni_dettagli_relazione(relation)
        self.add_to_history("delete", relazione_details)

        confirm = QMessageBox.question(
            self, "Delete Relationship",
            "Are you sure you want to delete this relationship?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            relation_manager.removeRelation(relazione_id)
            self.carica_lista_relazioni()
            QMessageBox.information(self, "Delete", "Relationship deleted successfully!")

    def crea_nuova_relazione(self):
        """Create a new relationship."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Relationship")
        layout = QFormLayout()

        nome_relazione = QLineEdit()
        layer_padre = self._crea_layer_combo(None)
        layer_figlio = self._crea_layer_combo(None)

        chiavi_padre = self._crea_field_combo(layer_padre.currentText(), None)
        chiavi_figlio = self._crea_field_combo(layer_figlio.currentText(), None)

        layout.addRow("Relationship Name:", nome_relazione)
        layout.addRow("Parent Layer:", layer_padre)
        layout.addRow("Child Layer:", layer_figlio)
        layout.addRow("Parent Key:", chiavi_padre)
        layout.addRow("Child Key:", chiavi_figlio)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        # Connect the confirm button
        buttonBox.accepted.connect(lambda: self.crea_relazione_esistente({
            'nome': nome_relazione.text(),
            'layer_padre': layer_padre.currentText(),
            'layer_figlio': layer_figlio.currentText(),
            'chiavi': {chiavi_padre.currentText(): chiavi_figlio.currentText()}
        }))
        buttonBox.rejected.connect(dialog.reject)

        dialog.exec()

    def crea_relazione_esistente(self, nuova_relazione):
        """Create a new relationship in the project."""
        project = QgsProject.instance()

        # Verifica l'esistenza dei layer
        layer_figlio = project.mapLayersByName(nuova_relazione['layer_figlio'])
        layer_padre = project.mapLayersByName(nuova_relazione['layer_padre'])

        if not layer_figlio or not layer_padre:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return False

        layer_figlio = layer_figlio[0]
        layer_padre = layer_padre[0]

        # Genera un ID univoco basato sul nome del layer e il nome della relazione
        relation_id = nuova_relazione['id']

        # Crea la relazione
        relation = QgsRelation()
        relation.setName(nuova_relazione['nome'])
        relation.setId(relation_id)
        relation.setReferencingLayer(layer_figlio.id())
        relation.setReferencedLayer(layer_padre.id())

        # Aggiungi le coppie di chiavi
        for chiave_padre, chiave_figlio in nuova_relazione['chiavi'].items():
            if chiave_padre in [field.name() for field in layer_padre.fields()] and chiave_figlio in [field.name() for field in layer_figlio.fields()]:
                relation.addFieldPair(chiave_padre, chiave_figlio)
            else:
                QMessageBox.warning(self, "Error", f"Key fields not found: {chiave_padre}, {chiave_figlio}")
                return False

        # Aggiungi la relazione al manager delle relazioni
        relation_manager = project.relationManager()
        relation_manager.addRelation(relation)

        # Aggiorna la visualizzazione delle relazioni e salva il progetto
        self.carica_lista_relazioni()
        self.add_to_history(f"Created new relationship: {nuova_relazione['nome']}")
        project.setDirty(True)
        project.write()

        QMessageBox.information(self, "Create", "Relationship created successfully!")
        return True



    def visualizza_storico(self):
        """Show the history of relationship modifications."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Modification History")
        layout = QVBoxLayout(dlg)

        history_list = QListWidget()
        for timestamp, action, details in self.history:
            history_list.addItem(f'{timestamp}: {action} - {details["nome"]}')
        layout.addWidget(history_list)

        rollback_button = QPushButton("Rollback to Selected")
        layout.addWidget(rollback_button)
        dlg.setLayout(layout)

        rollback_button.clicked.connect(lambda: self.rollback_modifica(history_list.currentRow(), history_list))
        dlg.exec_()

    def rollback_modifica(self, history_index, history_list_widget):
        """Rollback to a previous relationship modification."""
        if history_index < 0 or history_index >= len(self.history):
            QMessageBox.warning(self, "Error", "Please select a valid history item.")
            return

        timestamp, action, details = self.history[history_index]

        if action == "create":
            # Undo create by deleting the relationship
            project = QgsProject.instance()
            relation_manager = project.relationManager()
            relazione_id = None
            for rel_id, rel in relation_manager.relations().items():
                if rel.name() == details['nome']:
                    relazione_id = rel_id
                    break
            if relazione_id:
                relation_manager.removeRelation(relazione_id)
                self.carica_lista_relazioni()
                QMessageBox.information(self, "Rollback", f"Created relationship '{details['nome']}' has been deleted.")
        elif action == "delete":
            # Undo delete by recreating the relationship
            project = QgsProject.instance()
            relation_manager = project.relationManager()

            # Check if the relationship already exists to avoid duplicates
            if not relation_manager.relation(details['id']):
                relation = QgsRelation()
                relation.setName(details['nome'])
                relation.setId(details['id'])
                relation.setReferencingLayer(project.mapLayersByName(details['layer_figlio'])[0].id())
                relation.setReferencedLayer(project.mapLayersByName(details['layer_padre'])[0].id())

                for chiave_padre, chiave_figlio in details['chiavi'].items():
                    relation.addFieldPair(chiave_padre, chiave_figlio)

                relation_manager.addRelation(relation)
                self.carica_lista_relazioni()
                QMessageBox.information(self, "Rollback", f"Deleted relationship '{details['nome']}' has been restored.")
        elif action == "edit":
            # Undo edit by reverting to previous details
            project = QgsProject.instance()
            relation_manager = project.relationManager()
            relazione_id = details['id']

            # Remove the current version
            relation_manager.removeRelation(relazione_id)

            # Recreate the old version
            relation = QgsRelation()
            relation.setName(details['nome'])
            relation.setId(relazione_id)
            relation.setReferencingLayer(project.mapLayersByName(details['layer_figlio'])[0].id())
            relation.setReferencedLayer(project.mapLayersByName(details['layer_padre'])[0].id())

            for chiave_padre, chiave_figlio in details['chiavi'].items():
                relation.addFieldPair(chiave_padre, chiave_figlio)

            relation_manager.addRelation(relation)
            self.carica_lista_relazioni()
            QMessageBox.information(self, "Rollback", f"Edit to relationship '{details['nome']}' has been reverted.")
        elif action == "duplicate":
            # Undo duplicate by deleting the duplicated relationship
            project = QgsProject.instance()
            relation_manager = project.relationManager()
            relazione_id = None
            for rel_id, rel in relation_manager.relations().items():
                if rel.name() == details['nome']:
                    relazione_id = rel_id
                    break
            if relazione_id:
                relation_manager.removeRelation(relazione_id)
                self.carica_lista_relazioni()
                QMessageBox.information(self, "Rollback", f"Duplicated relationship '{details['nome']}' has been deleted.")

    def ottieni_relazioni(self):
        """Get all relationships in the project."""
        relazioni = {}
        project = QgsProject.instance()
        relation_manager = project.relationManager()

        for relation_id, relation in relation_manager.relations().items():
            # Verifica che `relation` sia effettivamente un oggetto QgsRelation
            if isinstance(relation, QgsRelation):
                relazioni[relation.id()] = {
                    'nome': relation.name(),
                    'referencing_layer': relation.referencingLayer().name(),
                    'referenced_layer': relation.referencedLayer().name(),
                    'chiavi': relation.fieldPairs()
                }
            else:
                print(f"Warning: Relation with ID {relation_id} is not a valid QgsRelation object.")
        
        return relazioni

    def ottieni_dettagli_relazione(self, relation):
        """Retrieve details of a specific relation."""
        if not relation:
            return {}

        project = QgsProject.instance()
        
        # Trova i layer padre e figlio dalla relazione
        layer_padre = project.mapLayer(relation.referencedLayerId())
        layer_figlio = project.mapLayer(relation.referencingLayerId())
        
        # Assicurati che i layer siano validi
        if not layer_padre or not layer_figlio:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return {}

        # Ottieni le coppie di chiavi
        field_pairs = relation.fieldPairs()
        chiavi = {key: value for key, value in field_pairs.items()}

        return {
            'id': relation.id(),  # Aggiungi l'ID della relazione
            'nome': relation.name(),
            'layer_padre': layer_padre.name(),
            'layer_figlio': layer_figlio.name(),
            'chiavi': chiavi
        }

    def modifica_relazione_esistente(self, relazione_id, nuova_relazione):
        """Edit an existing relationship."""
        project = QgsProject.instance()
        relation_manager = project.relationManager()

        # Get the existing relationship details before modification
        relazione_corrente = relation_manager.relation(relazione_id)
        dettagli_correnti = self.ottieni_dettagli_relazione(relazione_corrente)
        self.add_to_history("edit", dettagli_correnti)

        # Remove the existing relationship
        relation_manager.removeRelation(relazione_id)

        # Create a new relationship with updated parameters
        layer_figlio = project.mapLayersByName(nuova_relazione['layer_figlio'])[0]
        layer_padre = project.mapLayersByName(nuova_relazione['layer_padre'])[0]

        relation = QgsRelation()
        relation.setName(nuova_relazione['nome'])
        relation.setId(relazione_id)
        relation.setReferencingLayer(layer_figlio.id())
        relation.setReferencedLayer(layer_padre.id())

        for chiave_padre, chiave_figlio in nuova_relazione['chiavi'].items():
            relation.addFieldPair(chiave_padre, chiave_figlio)

        relation_manager.addRelation(relation)
        self.carica_lista_relazioni()
        QMessageBox.information(self, "Edit", "Relationship modified successfully!")

    def crea_relazione_esistente(self, nuova_relazione):
        """Create a new relationship in the project."""
        project = QgsProject.instance()

        # Verifica l'esistenza dei layer
        layer_figlio = project.mapLayersByName(nuova_relazione['layer_figlio'])
        layer_padre = project.mapLayersByName(nuova_relazione['layer_padre'])

        if not layer_figlio or not layer_padre:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return

        layer_figlio = layer_figlio[0]  # Seleziona il primo layer corrispondente
        layer_padre = layer_padre[0]

        # Genera un ID univoco basato sul nome del layer e il nome della relazione
        relation_id = f"{layer_padre.id()}_{layer_figlio.id()}_{nuova_relazione['nome']}".replace(' ', '_').lower()

        # Crea la relazione
        relation = QgsRelation()
        relation.setName(nuova_relazione['nome'])
        relation.setId(relation_id)  # Imposta l'ID univoco
        relation.setReferencingLayer(layer_figlio.id())
        relation.setReferencedLayer(layer_padre.id())

        # Aggiungi le coppie di chiavi
        for chiave_padre, chiave_figlio in nuova_relazione['chiavi'].items():
            if chiave_padre in [field.name() for field in layer_padre.fields()] and chiave_figlio in [field.name() for field in layer_figlio.fields()]:
                relation.addFieldPair(chiave_padre, chiave_figlio)
            else:
                QMessageBox.warning(self, "Error", f"Key fields not found: {chiave_padre}, {chiave_figlio}")
                return

        # Aggiungi la relazione al manager delle relazioni
        relation_manager = project.relationManager()
        relation_manager.addRelation(relation)

        # Aggiorna la lista delle relazioni e salva il progetto
        self.carica_lista_relazioni()
        self.add_to_history(f"Created new relationship: {nuova_relazione['nome']}", nuova_relazione)

        # Salvataggio esplicito del progetto
        project.setDirty(True)
        project.write()

        QMessageBox.information(self, "Create", "Relationship created successfully!")



    def add_to_history(self, action, dettagli):
        """Add an action to the modification history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append((timestamp, action, dettagli))

    def _crea_layer_combo(self, layer_name_preselezionato):
        """Create a combobox to select layers in the project."""
        combo = QComboBox()
        project = QgsProject.instance()
        found = False

        for layer in project.mapLayers().values():
            combo.addItem(layer.name())
            if layer.name() == layer_name_preselezionato:
                combo.setCurrentText(layer.name())
                found = True

        # Se il layer pre-selezionato non è stato trovato, segnala un avviso
        if not found:
            QMessageBox.warning(self, "Layer Not Found", f"Layer '{layer_name_preselezionato}' not found in the project.")
        
        return combo

    def _crea_field_combo(self, layer_name, chiave_preselezionata):
        """Create a combobox to select key fields."""
        combo = QComboBox()
        project = QgsProject.instance()
        if layer_name:
            layer = project.mapLayersByName(layer_name)[0]
            for field in layer.fields():
                combo.addItem(field.name())
                if chiave_preselezionata and field.name() == chiave_preselezionata:
                    combo.setCurrentText(field.name())
        return combo

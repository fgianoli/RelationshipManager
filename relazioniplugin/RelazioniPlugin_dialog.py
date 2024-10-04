# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, QFileDialog, 
                             QMessageBox, QInputDialog, QComboBox, QLabel, QFormLayout, 
                             QDialogButtonBox, QLineEdit)
from PyQt5.QtGui import QIcon
from qgis.core import QgsProject, QgsRelation
import json
from datetime import datetime

class RelazioniPluginDialog(QDialog):
    def __init__(self):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Relationship Manager")

        # Set plugin icon
        self.setWindowIcon(QIcon(':/plugins/relazioniplugin/icon.png'))

        # Create layout and widgets manually with Tab Layout
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

        self.btnStorico = QPushButton(QIcon(':/plugins/relazioniplugin/history.png'), "View History")
        layout.addWidget(self.btnStorico)

        self.setLayout(layout)

        # Connect buttons to their functions
        self.btnEsporta.clicked.connect(self.esporta_relazioni)
        self.btnCarica.clicked.connect(self.carica_relazioni)
        self.btnModifica.clicked.connect(self.apri_modifica_relazione)
        self.btnDuplica.clicked.connect(self.duplica_relazione)
        self.btnElimina.clicked.connect(self.elimina_relazione)
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
        if file_path:
            with open(file_path, 'r') as file:
                relazioni = json.load(file)

            project = QgsProject.instance()
            for relazione_id, relazione in relazioni.items():
                layer_figlio = project.mapLayersByName(relazione['layer_figlio'])[0]
                layer_padre = project.mapLayersByName(relazione['layer_padre'])[0]

                relation = QgsRelation()
                relation.setName(relazione['nome'])
                relation.setId(relazione_id)
                relation.setReferencingLayer(layer_figlio.id())
                relation.setReferencedLayer(layer_padre.id())

                for chiave_padre, chiave_figlio in relazione['chiavi'].items():
                    relation.addFieldPair(chiave_padre, chiave_figlio)

                project.relationManager().addRelation(relation)

            self.carica_lista_relazioni()
            QMessageBox.information(self, "Load", "Relationships loaded successfully!")

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

        # Open the dialog to modify the relationship
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Relationship")
        layout = QFormLayout()

        # Pre-fill data
        nome_relazione = QLineEdit(relation.name())
        layer_padre = self._crea_layer_combo(relation.referencedLayerId())
        layer_figlio = self._crea_layer_combo(relation.referencingLayerId())

        chiavi_padre = self._crea_field_combo(layer_padre.currentText(), list(relation.fieldPairs().keys())[0])
        chiavi_figlio = self._crea_field_combo(layer_figlio.currentText(), list(relation.fieldPairs().values())[0])

        layout.addRow("Relationship Name:", nome_relazione)
        layout.addRow("Parent Layer:", layer_padre)
        layout.addRow("Child Layer:", layer_figlio)
        layout.addRow("Parent Key:", chiavi_padre)
        layout.addRow("Child Key:", chiavi_figlio)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        # Connect the confirm button
        buttonBox.accepted.connect(lambda: self.modifica_relazione_esistente(relazione_id, {
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

        nuovo_nome, ok = QInputDialog.getText(self, "Duplicate Relationship", "Enter new relationship name:")
        if not ok or not nuovo_nome:
            return

        # Duplicate the relationship
        nuova_relazione = {
            'nome': nuovo_nome,
            'layer_figlio': relation.referencingLayer().name(),
            'layer_padre': relation.referencedLayer().name(),
            'chiavi': relation.fieldPairs()
        }
        self.modifica_relazione_esistente(relazione_id, nuova_relazione)

        QMessageBox.information(self, "Duplicate", "Relationship duplicated successfully!")

    def elimina_relazione(self):
        """Delete the selected relationship."""
        selected = self.listaRelazioni.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a relationship to delete.")
            return

        relazione_id = selected.text().split(":")[0]
        project = QgsProject.instance()
        relation_manager = project.relationManager()

        confirm = QMessageBox.question(self, "Delete Relationship", "Are you sure you want to delete this relationship?", 
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            relation_manager.removeRelation(relazione_id)
            self.carica_lista_relazioni()
            self.add_to_history(f"Deleted relationship: {relazione_id}")
            QMessageBox.information(self, "Delete", "Relationship deleted successfully!")

    def visualizza_storico(self):
        """Show the history of relationship modifications."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Modification History")
        layout = QVBoxLayout(dlg)

        history_list = QListWidget()
        for index, (timestamp, action, _) in enumerate(self.history):
            history_list.addItem(f'{timestamp}: {action}')
        
        layout.addWidget(history_list)
        
        # Add rollback button
        rollback_button = QPushButton("Rollback to selected change")
        layout.addWidget(rollback_button)
        dlg.setLayout(layout)

        rollback_button.clicked.connect(lambda: self.rollback_modifica(history_list.currentRow()))
        
        dlg.exec_()

    def rollback_modifica(self, history_index):
        """Rollback to a previous relationship modification."""
        if history_index < 0 or history_index >= len(self.history):
            QMessageBox.warning(self, "Error", "Please select a valid history item.")
            return
        
        # Get the details of the old relationship
        _, _, old_relation_details = self.history[history_index]
        
        # Reapply the old relationship details
        self.modifica_relazione_esistente(old_relation_details['id'], old_relation_details)
        QMessageBox.information(self, "Rollback", "The relationship has been restored to a previous version.")

    def ottieni_relazioni(self):
        """Get all relationships in the project."""
        relazioni = {}
        project = QgsProject.instance()
        for relation in project.relationManager().relations():
            relazioni[relation.id()] = {
                'name': relation.name(),
                'referencing_layer': relation.referencingLayer().name(),
                'referenced_layer': relation.referencedLayer().name(),
                'keys': relation.fieldPairs()
            }
        return relazioni

    def modifica_relazione_esistente(self, relazione_id, nuova_relazione):
        """Edit an existing relationship."""
        project = QgsProject.instance()
        relation_manager = project.relationManager()

        # Get the old relationship details before modifying
        relation = relation_manager.relation(relazione_id)
        old_relation_details = {
            'id': relazione_id,
            'nome': relation.name(),
            'layer_figlio': relation.referencingLayer().name(),
            'layer_padre': relation.referencedLayer().name(),
            'chiavi': relation.fieldPairs()
        }

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

        # Add the action to history with old relation details
        self.add_to_history(f"Edited relationship: {relazione_id}", old_relation_details)

        QMessageBox.information(self, "Edit", "Relationship modified successfully!")

    def add_to_history(self, action, relation_details):
        """Add an action to the modification history, saving the relationship details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append((timestamp, action, relation_details))

    def _crea_layer_combo(self, layer_id_preselezionato):
        """Create a combobox to select layers in the project."""
        combo = QComboBox()
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            combo.addItem(layer.name())
            if layer.id() == layer_id_preselezionato:
                combo.setCurrentText(layer.name())
        return combo

    def _crea_field_combo(self, layer_name, chiave_preselezionata):
        """Create a combobox to select key fields."""
        combo = QComboBox()
        project = QgsProject.instance()
        layer = project.mapLayersByName(layer_name)[0]
        for field in layer.fields():
            combo.addItem(field.name())
            if field.name() == chiave_preselezionata:
                combo.setCurrentText(field.name())
        return combo

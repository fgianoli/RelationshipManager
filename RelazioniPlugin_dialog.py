from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog,
    QMessageBox, QInputDialog, QComboBox, QLabel, QFormLayout,
    QDialogButtonBox, QLineEdit, QTabWidget, QWidget, QTextEdit,
    QGroupBox, QSizePolicy, QAbstractItemView
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSize
from qgis.core import QgsProject, QgsRelation, QgsApplication, Qgis, QgsVectorLayer
import json
import uuid
from datetime import datetime

# Qt5/Qt6 enum compatibility
try:
    _SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
except AttributeError:
    _SingleSelection = QAbstractItemView.SingleSelection

try:
    _BtnOk = QDialogButtonBox.StandardButton.Ok
    _BtnCancel = QDialogButtonBox.StandardButton.Cancel
except AttributeError:
    _BtnOk = QDialogButtonBox.Ok
    _BtnCancel = QDialogButtonBox.Cancel

try:
    _MsgYes = QMessageBox.StandardButton.Yes
    _MsgNo = QMessageBox.StandardButton.No
except AttributeError:
    _MsgYes = QMessageBox.Yes
    _MsgNo = QMessageBox.No


class RelazioniPluginDialog(QDialog):
    def __init__(self):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Relationship Manager")
        self.setMinimumSize(520, 550)

        # Set plugin icon
        self.setWindowIcon(QIcon(':/plugins/relazioniplugin/icon.png'))

        # Crea il layout principale e aggiungi il TabWidget
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab per la gestione delle relazioni
        tab_relazioni = QWidget()
        tab_relazioni_layout = QVBoxLayout()

        # Relationships list with label
        self.lblContatore = QLabel("Project relationships:")
        tab_relazioni_layout.addWidget(self.lblContatore)

        self.listaRelazioni = QListWidget()
        self.listaRelazioni.setAlternatingRowColors(True)
        self.listaRelazioni.setSelectionMode(_SingleSelection)
        tab_relazioni_layout.addWidget(self.listaRelazioni)

        # --- Gruppo: Gestione relazioni ---
        grp_gestione = QGroupBox("Manage")
        grp_gestione_layout = QHBoxLayout()

        self.btnCrea = QPushButton(QgsApplication.getThemeIcon('/mActionAdd.svg'), " Create")
        self.btnCrea.setToolTip("Create a new 1:N relationship between two layers")
        self.btnCrea.setIconSize(QSize(20, 20))
        grp_gestione_layout.addWidget(self.btnCrea)

        self.btnModifica = QPushButton(QgsApplication.getThemeIcon('/mActionToggleEditing.svg'), " Edit")
        self.btnModifica.setToolTip("Edit the selected relationship")
        self.btnModifica.setIconSize(QSize(20, 20))
        grp_gestione_layout.addWidget(self.btnModifica)

        self.btnDuplica = QPushButton(QgsApplication.getThemeIcon('/mActionEditCopy.svg'), " Duplicate")
        self.btnDuplica.setToolTip("Create a copy of the selected relationship with a new name")
        self.btnDuplica.setIconSize(QSize(20, 20))
        grp_gestione_layout.addWidget(self.btnDuplica)

        self.btnElimina = QPushButton(QgsApplication.getThemeIcon('/mActionDeleteSelected.svg'), " Delete")
        self.btnElimina.setToolTip("Delete the selected relationship")
        self.btnElimina.setIconSize(QSize(20, 20))
        grp_gestione_layout.addWidget(self.btnElimina)

        grp_gestione.setLayout(grp_gestione_layout)
        tab_relazioni_layout.addWidget(grp_gestione)

        # --- Gruppo: Import/Export ---
        grp_file = QGroupBox("Import / Export")
        grp_file_layout = QHBoxLayout()

        self.btnEsporta = QPushButton(QgsApplication.getThemeIcon('/mActionFileSaveAs.svg'), " Export to JSON")
        self.btnEsporta.setToolTip("Export all relationships to a JSON file")
        self.btnEsporta.setIconSize(QSize(20, 20))
        grp_file_layout.addWidget(self.btnEsporta)

        self.btnCarica = QPushButton(QgsApplication.getThemeIcon('/mActionFileOpen.svg'), " Load from JSON")
        self.btnCarica.setToolTip("Import relationships from a JSON file")
        self.btnCarica.setIconSize(QSize(20, 20))
        grp_file_layout.addWidget(self.btnCarica)

        grp_file.setLayout(grp_file_layout)
        tab_relazioni_layout.addWidget(grp_file)

        # --- Bottone storico ---
        self.btnStorico = QPushButton(QgsApplication.getThemeIcon('/mActionUndo.svg'), " View History / Rollback")
        self.btnStorico.setToolTip("View modification history and rollback changes")
        self.btnStorico.setIconSize(QSize(20, 20))
        tab_relazioni_layout.addWidget(self.btnStorico)

        # Imposta il layout della tab "Relazioni"
        tab_relazioni.setLayout(tab_relazioni_layout)

        # Tab per l'help
        tab_help = QWidget()
        help_layout = QVBoxLayout()

        # Casella di testo per mostrare l'help
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.5; }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 20px; }
                h3 { color: #7f8c8d; }
                .feature { background-color: #ecf0f1; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }
                .tip { background-color: #d5f5e3; padding: 10px; margin: 10px 0; border-left: 4px solid #27ae60; }
                .warning { background-color: #fcf3cf; padding: 10px; margin: 10px 0; border-left: 4px solid #f39c12; }
                .example { background-color: #e8f6f3; padding: 10px; margin: 10px 0; font-family: monospace; }
                code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
            </style>

            <h1>🔗 Relationship Manager Plugin</h1>
            <p><b>Version 1.3</b> - Manage layer relationships in your QGIS projects with ease.</p>

            <h2>📋 What are Relationships?</h2>
            <p>Relationships in QGIS connect features from different layers using key fields.
            For example, you can link a <i>Buildings</i> layer to a <i>Addresses</i> layer
            using a common field like <code>building_id</code>.</p>

            <div class="tip">
                <b>💡 Tip:</b> Relationships enable powerful features like automatic forms with
                related records, and are essential for working with relational databases.
            </div>

            <h2>🛠️ Features</h2>

            <div class="feature">
                <h3>➕ Create Relationship</h3>
                <p>Create a new relationship between two layers:</p>
                <ol>
                    <li>Click <b>"Create Relationship"</b></li>
                    <li>Enter a name for the relationship</li>
                    <li>Select the <b>Parent Layer</b> (the "one" side, e.g., Buildings)</li>
                    <li>Select the <b>Child Layer</b> (the "many" side, e.g., Apartments)</li>
                    <li>Choose the <b>Key Fields</b> that link the two layers</li>
                    <li>Click OK to create</li>
                </ol>
            </div>

            <div class="feature">
                <h3>📤 Export Relationships</h3>
                <p>Save all project relationships to a JSON file. Useful for:</p>
                <ul>
                    <li>Backing up your relationship configuration</li>
                    <li>Sharing relationships with colleagues</li>
                    <li>Reusing the same structure in other projects</li>
                </ul>
            </div>

            <div class="feature">
                <h3>📥 Load Relationships</h3>
                <p>Import relationships from a previously exported JSON file.</p>
                <div class="warning">
                    <b>⚠️ Note:</b> The layers referenced in the JSON must exist in the
                    current project with the same names.
                </div>
            </div>

            <div class="feature">
                <h3>✏️ Edit Relationship</h3>
                <p>Modify an existing relationship. Select it from the list and click
                <b>"Edit Relationship"</b> to change its name, layers, or key fields.</p>
            </div>

            <div class="feature">
                <h3>📋 Duplicate Relationship</h3>
                <p>Create a copy of an existing relationship with a new name.
                Useful when creating similar relationships.</p>
            </div>

            <div class="feature">
                <h3>🗑️ Delete Relationship</h3>
                <p>Remove a relationship from the project. This action can be undone
                using the History feature.</p>
            </div>

            <div class="feature">
                <h3>📜 View History</h3>
                <p>See all changes made during this session and rollback if needed.</p>
            </div>

            <h2>📖 Example: Building-Apartment Relationship</h2>
            <div class="example">
                <b>Scenario:</b> Link buildings to their apartments<br><br>
                <b>Parent Layer:</b> buildings (with field <code>building_id</code>)<br>
                <b>Child Layer:</b> apartments (with field <code>fk_building</code>)<br>
                <b>Parent Key:</b> building_id<br>
                <b>Child Key:</b> fk_building<br><br>
                This creates a 1:N relationship where each building can have many apartments.
            </div>

            <h2>🔧 Troubleshooting</h2>

            <div class="warning">
                <h3>❌ "Key fields not found"</h3>
                <p>This error occurs when the selected field doesn't exist in the layer. Check that:</p>
                <ul>
                    <li>Field names are spelled correctly (case-sensitive)</li>
                    <li>You selected the correct layer</li>
                    <li>The field exists in both layers</li>
                </ul>
            </div>

            <div class="warning">
                <h3>❌ Relationship shows as "(INVALID)"</h3>
                <p>The relationship configuration is incorrect. Common causes:</p>
                <ul>
                    <li>One of the layers was removed from the project</li>
                    <li>A key field was renamed or deleted</li>
                    <li>Layer IDs changed (can happen when re-adding layers)</li>
                </ul>
                <p><b>Solution:</b> Delete the invalid relationship and recreate it.</p>
            </div>

            <div class="warning">
                <h3>❌ Relationships not loading from JSON</h3>
                <p>When importing, ensure that:</p>
                <ul>
                    <li>All referenced layers exist in the current project</li>
                    <li>Layer names match exactly (case-sensitive)</li>
                    <li>Key fields exist in the layers</li>
                </ul>
            </div>

            <h2>💡 Best Practices</h2>
            <ul>
                <li>Use meaningful relationship names (e.g., "building_has_apartments")</li>
                <li>Export relationships regularly as backup</li>
                <li>Use consistent naming conventions for key fields</li>
                <li>Supported key field types: Integer, String, UUID, and more</li>
            </ul>

            <h2>📞 Support</h2>
            <p>For bug reports and feature requests, please visit the plugin repository on GitHub.</p>

            <hr>
            <p style="color: #7f8c8d; font-size: 0.9em;">
                Relationship Manager Plugin v1.3<br>
                License: GPL v3
            </p>
            """)
        help_layout.addWidget(help_text)
        tab_help.setLayout(help_layout)

        # Aggiungi le tab al TabWidget
        self.tabs.addTab(tab_relazioni, "Relation Manager")
        self.tabs.addTab(tab_help, "Help")

        # Aggiungi il TabWidget al layout principale
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Collega i pulsanti alle loro funzioni
        self.btnEsporta.clicked.connect(self.esporta_relazioni)
        self.btnCarica.clicked.connect(self.carica_relazioni)
        self.btnModifica.clicked.connect(self.apri_modifica_relazione)
        self.btnDuplica.clicked.connect(self.duplica_relazione)
        self.btnElimina.clicked.connect(self.elimina_relazione)
        self.btnCrea.clicked.connect(self.crea_nuova_relazione)
        self.btnStorico.clicked.connect(self.visualizza_storico)

        # Inizializza la cronologia
        self.history = []

        # Connect to project change signals to refresh the list
        QgsProject.instance().cleared.connect(self.on_project_changed)
        QgsProject.instance().readProject.connect(self.on_project_changed)

        # Carica le relazioni all'avvio
        self.carica_lista_relazioni()

    def on_project_changed(self):
        """Handle project change - clear and reload relations list."""
        self.history = []
        self.carica_lista_relazioni()

    def carica_lista_relazioni(self):
        """List all relationships in the QGIS project."""
        self.listaRelazioni.clear()
        project = QgsProject.instance()

        relation_manager = project.relationManager()

        for relation in relation_manager.relations().values():
            try:
                is_composition = (
                    relation.strength()
                    == Qgis.RelationshipStrength.Composition
                )
                strength_label = (
                    "Composition" if is_composition else "Association"
                )
                label = (
                    f'{relation.id()}: '
                    f'{relation.name()} [{strength_label}]'
                )
                if not relation.isValid():
                    label += ' (INVALID)'
                self.listaRelazioni.addItem(label)
            except Exception:
                self.listaRelazioni.addItem(
                    f'{relation.id()}: (BROKEN RELATION)'
                )

        count = self.listaRelazioni.count()
        self.lblContatore.setText(f"Project relationships: {count}")

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
            return

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
            relation.setId(relazione_id)
            relation.setReferencingLayer(layer_figlio.id())
            relation.setReferencedLayer(layer_padre.id())

            # Imposta il tipo di relazione (sketcher) se presente nel JSON
            if 'sketcher' in relazione:
                relation.setStrength(
                    Qgis.RelationshipStrength(relazione['sketcher'])
                )

            # Aggiungi le coppie di chiavi
            # fieldPairs() exports as {referencing_field: referenced_field} = {child: parent}
            valid_keys = True
            for chiave_figlio, chiave_padre in relazione['chiavi'].items():
                if chiave_figlio in layer_figlio.fields().names() and chiave_padre in layer_padre.fields().names():
                    relation.addFieldPair(chiave_figlio, chiave_padre)
                else:
                    relazioni_fallite.append(f"Invalid key pair: {chiave_padre} -> {chiave_figlio} in relationship '{relazione['nome']}'")
                    valid_keys = False
                    break

            # Aggiungi la relazione al manager se le chiavi sono valide
            if valid_keys:
                if relation_manager.addRelation(relation) or relation_manager.relation(relazione_id):
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

        relation = QgsProject.instance().relationManager().relation(relazione_id)
        if not relation:
            QMessageBox.warning(self, "Error", "Relationship not found.")
            return

        relazione_details = self.ottieni_dettagli_relazione(relation)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Relationship: {relazione_details['id']}")
        layout = QFormLayout()

        nome_relazione = QLineEdit(relazione_details['nome'])
        layer_padre = self._crea_layer_combo(relazione_details['layer_padre'])
        layer_figlio = self._crea_layer_combo(relazione_details['layer_figlio'])

        # chiavi from ottieni_dettagli_relazione uses fieldPairs() = {child: parent}
        chiavi_keys = list(relazione_details['chiavi'].keys())    # referencing/child fields
        chiavi_values = list(relazione_details['chiavi'].values())  # referenced/parent fields

        chiavi_padre = self._crea_field_combo(layer_padre.currentText(), chiavi_values[0] if chiavi_values else None)
        chiavi_figlio = self._crea_field_combo(layer_figlio.currentText(), chiavi_keys[0] if chiavi_keys else None)

        # Combobox per il tipo di relazione (strength)
        strength_combo = self._crea_strength_combo(relazione_details.get('sketcher'))

        # Aggiorna i campi quando cambia il layer selezionato
        layer_padre.currentTextChanged.connect(lambda name: self._aggiorna_field_combo(chiavi_padre, name))
        layer_figlio.currentTextChanged.connect(lambda name: self._aggiorna_field_combo(chiavi_figlio, name))

        layout.addRow("Relationship Name:", nome_relazione)
        layout.addRow("Parent Layer:", layer_padre)
        layout.addRow("Child Layer:", layer_figlio)
        layout.addRow("Parent Key:", chiavi_padre)
        layout.addRow("Child Key:", chiavi_figlio)
        layout.addRow("Strength:", strength_combo)

        buttonBox = QDialogButtonBox(_BtnOk | _BtnCancel)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        # chiavi dict uses QGIS convention: {referencing/child: referenced/parent}
        buttonBox.accepted.connect(lambda: self.modifica_relazione_esistente(relazione_details['id'], {
            'nome': nome_relazione.text(),
            'layer_padre': layer_padre.currentText(),
            'layer_figlio': layer_figlio.currentText(),
            'chiavi': {chiavi_figlio.currentText(): chiavi_padre.currentText()},
            'sketcher': strength_combo.currentData()
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

        layer_figlio = project.mapLayersByName(relation.referencingLayer().name())
        layer_padre = project.mapLayersByName(relation.referencedLayer().name())

        if not layer_figlio or not layer_padre:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return

        nuovo_nome, ok = QInputDialog.getText(self, "Duplicate Relationship", "Enter new relationship name:")
        if not ok or not nuovo_nome:
            return

        nuovo_id = f'duplicated_{relazione_id}_{str(uuid.uuid4())}'

        # fieldPairs() already returns {referencing/child: referenced/parent}
        nuova_relazione = {
            'id': nuovo_id,
            'nome': nuovo_nome,
            'layer_figlio': layer_figlio[0].name(),
            'layer_padre': layer_padre[0].name(),
            'chiavi': relation.fieldPairs(),
            'sketcher': relation.strength()
        }

        self.crea_relazione_esistente(nuova_relazione, registra_storia=False)

        self.add_to_history("duplicate", nuova_relazione)

        QMessageBox.information(self, "Duplicate", "Relationship duplicated successfully!")

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

        confirm = QMessageBox.question(
            self, "Delete Relationship",
            "Are you sure you want to delete this relationship?",
            _MsgYes | _MsgNo
        )
        if confirm == _MsgYes:
            # Save state to history only after user confirms deletion
            relazione_details = self.ottieni_dettagli_relazione(relation)
            self.add_to_history("delete", relazione_details)

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

        # Combobox per il tipo di relazione (strength)
        strength_combo = self._crea_strength_combo(None)

        # Aggiorna i campi quando cambia il layer selezionato
        layer_padre.currentTextChanged.connect(lambda name: self._aggiorna_field_combo(chiavi_padre, name))
        layer_figlio.currentTextChanged.connect(lambda name: self._aggiorna_field_combo(chiavi_figlio, name))

        layout.addRow("Relationship Name:", nome_relazione)
        layout.addRow("Parent Layer:", layer_padre)
        layout.addRow("Child Layer:", layer_figlio)
        layout.addRow("Parent Key:", chiavi_padre)
        layout.addRow("Child Key:", chiavi_figlio)
        layout.addRow("Strength:", strength_combo)

        buttonBox = QDialogButtonBox(_BtnOk | _BtnCancel)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        # chiavi dict uses QGIS convention: {referencing/child: referenced/parent}
        buttonBox.accepted.connect(lambda: self.crea_relazione_esistente({
            'nome': nome_relazione.text(),
            'layer_padre': layer_padre.currentText(),
            'layer_figlio': layer_figlio.currentText(),
            'chiavi': {chiavi_figlio.currentText(): chiavi_padre.currentText()},
            'sketcher': strength_combo.currentData()
        }))
        buttonBox.rejected.connect(dialog.reject)

        dialog.exec()

    def crea_relazione_esistente(self, nuova_relazione, registra_storia=True):
        """Create a new relationship in the project."""
        project = QgsProject.instance()

        # Verifica l'esistenza dei layer
        layer_figlio = project.mapLayersByName(nuova_relazione['layer_figlio'])
        layer_padre = project.mapLayersByName(nuova_relazione['layer_padre'])

        if not layer_figlio or not layer_padre:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return

        layer_figlio = layer_figlio[0]
        layer_padre = layer_padre[0]

        # Usa l'ID fornito oppure generane uno univoco
        relation_id = nuova_relazione.get('id') or f"{layer_padre.id()}_{layer_figlio.id()}_{nuova_relazione['nome']}".replace(' ', '_').lower()

        # Crea la relazione
        relation = QgsRelation()
        relation.setName(nuova_relazione['nome'])
        relation.setId(relation_id)
        relation.setReferencingLayer(layer_figlio.id())
        relation.setReferencedLayer(layer_padre.id())

        # Imposta il tipo di relazione (sketcher)
        sketcher = nuova_relazione.get('sketcher')
        if sketcher is not None:
            relation.setStrength(sketcher)

        # Aggiungi le coppie di chiavi
        # chiavi dict uses QGIS convention: {referencing/child: referenced/parent}
        for chiave_figlio, chiave_padre in nuova_relazione['chiavi'].items():
            if chiave_figlio in [field.name() for field in layer_figlio.fields()] and chiave_padre in [field.name() for field in layer_padre.fields()]:
                relation.addFieldPair(chiave_figlio, chiave_padre)
            else:
                QMessageBox.warning(self, "Error", f"Key fields not found: {chiave_padre} (parent), {chiave_figlio} (child)")
                return

        # Aggiungi la relazione al manager delle relazioni
        relation_manager = project.relationManager()
        relation_manager.addRelation(relation)

        # Aggiorna la lista delle relazioni e salva il progetto
        self.carica_lista_relazioni()

        if registra_storia:
            self.add_to_history("create", nuova_relazione)
            project.setDirty(True)
            project.write()
            QMessageBox.information(self, "Create", "Relationship created successfully!")



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
        dlg.exec()

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

            if not relation_manager.relation(details['id']):
                relation = QgsRelation()
                relation.setName(details['nome'])
                relation.setId(details['id'])
                relation.setReferencingLayer(project.mapLayersByName(details['layer_figlio'])[0].id())
                relation.setReferencedLayer(project.mapLayersByName(details['layer_padre'])[0].id())

                if 'sketcher' in details and details['sketcher'] is not None:
                    relation.setStrength(details['sketcher'])

                for chiave_figlio, chiave_padre in details['chiavi'].items():
                    relation.addFieldPair(chiave_figlio, chiave_padre)

                relation_manager.addRelation(relation)
                self.carica_lista_relazioni()
                QMessageBox.information(self, "Rollback", f"Deleted relationship '{details['nome']}' has been restored.")
        elif action == "edit":
            # Undo edit by reverting to previous details
            project = QgsProject.instance()
            relation_manager = project.relationManager()
            relazione_id = details['id']

            relation_manager.removeRelation(relazione_id)

            relation = QgsRelation()
            relation.setName(details['nome'])
            relation.setId(relazione_id)
            relation.setReferencingLayer(project.mapLayersByName(details['layer_figlio'])[0].id())
            relation.setReferencedLayer(project.mapLayersByName(details['layer_padre'])[0].id())

            if 'sketcher' in details and details['sketcher'] is not None:
                relation.setStrength(details['sketcher'])

            for chiave_figlio, chiave_padre in details['chiavi'].items():
                relation.addFieldPair(chiave_figlio, chiave_padre)

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
            if isinstance(relation, QgsRelation):
                relazioni[relation.id()] = {
                    'nome': relation.name(),
                    'referencing_layer': relation.referencingLayer().name(),
                    'referenced_layer': relation.referencedLayer().name(),
                    'chiavi': relation.fieldPairs(),
                    'sketcher': int(relation.strength())
                }
            else:
                print(f"Warning: Relation with ID {relation_id} is not a valid QgsRelation object.")

        return relazioni

    def ottieni_dettagli_relazione(self, relation):
        """Retrieve details of a specific relation."""
        if not relation:
            return {}

        project = QgsProject.instance()

        layer_padre = project.mapLayer(relation.referencedLayerId())
        layer_figlio = project.mapLayer(relation.referencingLayerId())

        if not layer_padre or not layer_figlio:
            QMessageBox.warning(self, "Error", "Parent or child layer not found.")
            return {}

        field_pairs = relation.fieldPairs()
        chiavi = {key: value for key, value in field_pairs.items()}

        return {
            'id': relation.id(),
            'nome': relation.name(),
            'layer_padre': layer_padre.name(),
            'layer_figlio': layer_figlio.name(),
            'chiavi': chiavi,
            'sketcher': relation.strength()
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

        # Imposta il tipo di relazione (sketcher)
        sketcher = nuova_relazione.get('sketcher')
        if sketcher is not None:
            relation.setStrength(sketcher)

        # chiavi dict uses QGIS convention: {referencing/child: referenced/parent}
        for chiave_figlio, chiave_padre in nuova_relazione['chiavi'].items():
            relation.addFieldPair(chiave_figlio, chiave_padre)

        relation_manager.addRelation(relation)
        self.carica_lista_relazioni()
        QMessageBox.information(self, "Edit", "Relationship modified successfully!")

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
            if not isinstance(layer, QgsVectorLayer):
                continue
            combo.addItem(layer.name())
            if layer.name() == layer_name_preselezionato:
                combo.setCurrentText(layer.name())
                found = True

        if not found and layer_name_preselezionato is not None:
            QMessageBox.warning(self, "Layer Not Found", f"Layer '{layer_name_preselezionato}' not found in the project.")

        return combo

    def _crea_field_combo(self, layer_name, chiave_preselezionata):
        """Create a combobox to select key fields."""
        combo = QComboBox()
        project = QgsProject.instance()
        if layer_name:
            layers = project.mapLayersByName(layer_name)
            if layers:
                for field in layers[0].fields():
                    combo.addItem(field.name())
                    if chiave_preselezionata and field.name() == chiave_preselezionata:
                        combo.setCurrentText(field.name())
        return combo

    def _aggiorna_field_combo(self, field_combo, layer_name):
        """Update the field combo box when the layer selection changes."""
        field_combo.clear()
        if layer_name:
            project = QgsProject.instance()
            layers = project.mapLayersByName(layer_name)
            if layers:
                for field in layers[0].fields():
                    field_combo.addItem(field.name())

    def _crea_strength_combo(self, sketcher_preselezionato):
        """Create a combobox to select the relationship strength (Association/Composition)."""
        combo = QComboBox()
        combo.addItem("Association", Qgis.RelationshipStrength.Association)
        combo.addItem("Composition", Qgis.RelationshipStrength.Composition)

        if sketcher_preselezionato is not None:
            if sketcher_preselezionato == Qgis.RelationshipStrength.Composition:
                combo.setCurrentIndex(1)
            else:
                combo.setCurrentIndex(0)

        return combo

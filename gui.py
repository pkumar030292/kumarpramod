import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QRadioButton, QButtonGroup, QLabel, QLineEdit, QMessageBox

class ConfigGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
    def initUI(self):
        # Initialize layout
        layout = QVBoxLayout()

        # Title
        self.title = QLabel("Network Config Generator", self)
        layout.addWidget(self.title)

        # File upload buttons
        self.upload_loopback_button = QPushButton('Upload loopback.csv', self)
        self.upload_loopback_button.clicked.connect(self.upload_loopback)
        layout.addWidget(self.upload_loopback_button)

        self.upload_wan_button = QPushButton('Upload wan.csv', self)
        self.upload_wan_button.clicked.connect(self.upload_wan)
        layout.addWidget(self.upload_wan_button)

        # Radio buttons for options
        self.radio_group = QButtonGroup(self)
        
        self.generate_all_sites = QRadioButton("Generate all config for all sites", self)
        self.radio_group.addButton(self.generate_all_sites)
        layout.addWidget(self.generate_all_sites)
        
        self.generate_one_site = QRadioButton("Generate all config for one site", self)
        self.radio_group.addButton(self.generate_one_site)
        layout.addWidget(self.generate_one_site)
        
        self.generate_individual = QRadioButton("Generate individual components for one site", self)
        self.radio_group.addButton(self.generate_individual)
        layout.addWidget(self.generate_individual)
        
        # Input for site ID (for single site options)
        self.site_id_label = QLabel("Enter Site ID:", self)
        self.site_id_input = QLineEdit(self)
        layout.addWidget(self.site_id_label)
        layout.addWidget(self.site_id_input)
        
        # Generate button
        self.generate_button = QPushButton('Generate', self)
        self.generate_button.clicked.connect(self.generate_config)
        layout.addWidget(self.generate_button)
        
        # Set the layout and window title
        self.setLayout(layout)
        self.setWindowTitle('Network Config Generator')

        # Disable site ID input initially
        self.site_id_label.setVisible(False)
        self.site_id_input.setVisible(False)
        
        # Connect radio buttons to functions
        self.generate_all_sites.toggled.connect(self.toggle_site_id_input)
        self.generate_one_site.toggled.connect(self.toggle_site_id_input)
        self.generate_individual.toggled.connect(self.toggle_site_id_input)
        
    def upload_loopback(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select loopback.csv file", "", "CSV Files (*.csv)", options=options)
        if file:
            self.loopback_file = file
            os.makedirs('input', exist_ok=True)
            os.rename(file, 'input/loopback.csv')
            QMessageBox.information(self, "File Uploaded", "loopback.csv uploaded successfully.")
    
    def upload_wan(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select wan.csv file", "", "CSV Files (*.csv)", options=options)
        if file:
            self.wan_file = file
            os.makedirs('input', exist_ok=True)
            os.rename(file, 'input/wan.csv')
            QMessageBox.information(self, "File Uploaded", "wan.csv uploaded successfully.")
    
    def toggle_site_id_input(self):
        if self.generate_all_sites.isChecked():
            self.site_id_label.setVisible(False)
            self.site_id_input.setVisible(False)
        else:
            self.site_id_label.setVisible(True)
            self.site_id_input.setVisible(True)
    
    def generate_config(self):
        if self.generate_all_sites.isChecked():
            self.run_script('area_generator.py')
            self.run_script('new_loopback_file.py')
            self.run_script('loopback.py')
            self.run_script('wan_final.py')
            self.run_script('ospf_cost.py')
            self.run_script('route_map_wip.py')
            self.run_script('bgp_new.py')
            self.run_script('RSVP.py')
            self.run_script('service_bgp.py')
            QMessageBox.information(self, "Success", "All configurations generated for all sites.")

        elif self.generate_one_site.isChecked():
            site_id = self.site_id_input.text().strip()
            if site_id:
                self.run_script('area_generator.py')
                self.run_script('new_loopback_file.py')
                self.run_script('loopback.py', site_id)
                self.run_script('wan_final.py', site_id)
                self.run_script('ospf_cost.py', site_id)
                self.run_script('route_map_wip.py', site_id)
                self.run_script('bgp_new.py', site_id)
                self.run_script('RSVP.py', site_id)
                self.run_script('service_bgp.py', site_id)
                QMessageBox.information(self, "Success", f"All configurations generated for site {site_id}.")
            else:
                QMessageBox.warning(self, "Error", "Please enter a valid Site ID.")
        
        elif self.generate_individual.isChecked():
            site_id = self.site_id_input.text().strip()
            if site_id:
                self.run_script('loopback.py', site_id)
                self.run_script('wan_final.py', site_id)
                self.run_script('ospf_cost.py', site_id)
                self.run_script('route_map_wip.py', site_id)
                self.run_script('bgp_new.py', site_id)
                self.run_script('RSVP.py', site_id)
                self.run_script('service_bgp.py', site_id)
                QMessageBox.information(self, "Success", f"Individual configurations generated for site {site_id}.")
            else:
                QMessageBox.warning(self, "Error", "Please enter a valid Site ID.")
    
    def run_script(self, script_name, site_id=None):
        if site_id:
            os.system(f'python {script_name} {site_id}')
        else:
            os.system(f'python {script_name}')
        

def main():
    app = QApplication(sys.argv)
    ex = ConfigGeneratorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

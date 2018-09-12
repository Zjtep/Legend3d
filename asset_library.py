# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import os
import sys
import threading
#
# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui

from .ui.dialog import Ui_Dialog

from tank_vendor import shotgun_api3

sg = shotgun_api3.Shotgun("https://legend.shotgunstudio.com", script_name="toolkit",
                          api_key="d0211b3fecd9b4f0141545e7fd07965a5331eee13842700f1b6477ecffba5977")
import logging
from os import walk
import csv
from pprint import PrettyPrinter

logger = sgtk.platform.get_logger(__name__)
import random
import string
import tempfile


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for launching
    # different types of windows. By using these methods, your windows will be correctly
    # decorated and handled in a consistent fashion by the system.

    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    # RENAME THIS
    app_instance.engine.show_dialog("tk-legend-shotgun-publish", app_instance, AppDialog)


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """
    PROJECT_ID = 88
    main_struct = []

    def __init__(self):
        super(AppDialog, self).__init__()

        self.initUI()

        # self.builtUI()
        # self.buildConnections()

    def initUI(self):
        # --- initiate ui components
        btn_publish_files = QtGui.QPushButton('Publish Files')

        lbl_folder = QtGui.QLabel('Folder:')
        self._lbl_display_folder = QtGui.QLineEdit('nothing selected')
        self._lbl_display_folder.setReadOnly(True)
        btn_browse_files = QtGui.QPushButton('...')

        btn_create_assets = QtGui.QPushButton('Create Assets')
        btn_create_sheet = QtGui.QPushButton('Create Sheet')

        lbl_asset_type = QtGui.QLabel('Type:')
        self._combo_entity_type = QtGui.QComboBox(self)

        result = sg.schema_field_read("Asset", "sg_asset_type")
        self._combo_entity_type.addItems(result['sg_asset_type']['properties']['valid_values']['value'])

        lbl_parent_assets = QtGui.QLabel('Parent Asset:')
        self._txt_parent_assets = QtGui.QLineEdit('Assets')

        lbl_asset_tags = QtGui.QLabel('Tags:')
        self._txt_asset_tag = QtGui.QLineEdit('Tags')
        completer = Completer_new()
        completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._txt_asset_tag.setCompleter(completer)

        model = QtGui.QStringListModel()
        completer.setModel(model)
        filters = [['id', 'greater_than', 0]]
        fields = ['name']
        temp_tag_list = sg.find('Tag', filters, fields)
        tag_list = []
        for t in temp_tag_list:
            tag_list.append(t['name'])
        model.setStringList(tag_list)

        # --- build the ui components
        layout = QtGui.QGridLayout(self)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(6)

        # addWidget (self, QWidget, int row, int column, int rowSpan, int columnSpan, Qt.Alignment alignment = 0)
        layout.addWidget(lbl_folder, 0, 0)
        layout.addWidget(self._lbl_display_folder, 0, 1, 1, 4)
        layout.addWidget(btn_browse_files, 0, 5)

        row = 1
        layout.addWidget(btn_create_sheet, row, 1)
        layout.addWidget(btn_create_assets, row, 2)

        row += 1
        layout.addWidget(lbl_asset_type, row, 0)
        # layout.addWidget(self.txt_type, row, 1, 1, 5)
        layout.addWidget(self._combo_entity_type, row, 1, 1, 5)

        row += 1
        layout.addWidget(lbl_parent_assets, row, 0)
        layout.addWidget(self._txt_parent_assets, row, 1, 1, 5)

        row += 1
        layout.addWidget(lbl_asset_tags, row, 0)
        layout.addWidget(self._txt_asset_tag, row, 1, 1, 5)

        row += 1
        layout.addWidget(btn_publish_files)

        logging_widget = QtGui.QSplitter()
        log_handler = QPlainTextEditLogger(logging_widget)
        logger.addHandler(log_handler)
        layout.addWidget(logging_widget, row, 1, 5, 5)
        logger.info('tk-legend-shotgun-publish running')

        # ---- connect some signals
        btn_publish_files.clicked.connect(self._publish_files)
        btn_browse_files.clicked.connect(self._browse_files)
        btn_create_sheet.clicked.connect(self._create_sheet)
        btn_create_assets.clicked.connect(self._create_assets)

        self.setGeometry(10, 20, 500, 100)
        self.setWindowTitle('Legend Shotgun Publish')  # Remember this to remind yourself not to mess up live scripts
        self.setLayout(layout)
        self.show()

    def _browse_files(self):
        """
        Select files for publish
        """

        result = self._on_browse()
        if result is not None:
            self.update_labels()

    def _create_sheet(self):
        """
        Create excel sheet 
        """
        random_key = ''.join(random.choice(string.digits) for i in range(10))
        # integrationPath = os.getenv('LOCALAPPDATA') + r"/Shotgun//temp/"

        integration_path = tempfile.gettempdir()
        # integration_path = r"V:/user/jzhu/temp/"
        integration_file = os.path.join(integration_path, "output%s.csv" % random_key)
        # integration_file = "%soutput%s.csv" % (integration_path, random_key)
        print integration_file
        header = ['Asset Name', 'Type', 'Task Template', 'Parent Asset', 'Project', 'Tags']

        self.update_main_struct()
        temp_list = []
        for x in self.main_struct:
            temp_list.append(x['Info'])
        with open(integration_file, 'wb') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writeheader()
            dict_writer.writerows(temp_list)
            # print integration_file
        logger.info('Creating CSV File...')
        logger.info(integration_file)

    def _create_assets(self):
        """
        Makes all shotgun entities
        creates tags
        """
        # self.create_tag()
        if len(self.main_struct) != 0:
            tag_list = self.create_tag()
            asset_list = self.create_parent_asset(tag_list)
            # print asset_list
            self.create_child_asset(tag_list, asset_list)
            logger.info('Done!')
            # print tag_list

        else:
            logger.info('Please Select An Assets...')
            # print "please select asset"

    def _publish_files(self):

        # PrettyPrinter(indent=4).pprint(self.main_struct)
        if (len(self.main_struct) != 0):
            if self.main_struct[0]['id'] != None:
                for t in self.main_struct:
                    version_dict = self.create_version(t)
                    publish_dict = self.create_publish(t)

                    data = {
                        'version': {'id': version_dict['id'],
                                    'name': t['FileName'],
                                    'type': 'Version'},
                        'entity': {'type': 'Asset', 'id': t['id']}
                    }

                    sg.update('PublishedFile', publish_dict['id'], data)

                    data_2 = {
                        'sg_published_files': [{'type': 'PublishedFile', 'id': publish_dict['id']}]
                    }
                    sg.update('Asset', t['id'], data_2)
                    logger.info('Done!')

            else:
                logger.info('Please Create An Assets...')
        else:
            logger.info('Please Select An Assets...')

            # version_dict = self.create_version()
            # publish_dict = self.create_publish()
            #
            # PrettyPrinter(indent=4).pprint(version_dict)
            # print""
            # PrettyPrinter(indent=4).pprint(publish_dict)
            #
            # data = {
            #     'version': {'id': version_dict['id'],
            #                 'name': '011_Electricity.mov',
            #                 'type': 'Version'},
            #     'entity': {'type': 'Asset', 'id': 1982}
            # }
            #
            # sg.update('PublishedFile', publish_dict['id'], data)
            #
            # data_2 = {
            #     'sg_published_files': [{'type': 'PublishedFile', 'id': publish_dict['id']}]
            # }
            # sg.update('Asset', 1982, data_2)

    def _on_browse(self):
        """
        Opens a file dialog to browse to files for publishing
        """
        # passG
        file_dialog = QtGui.QFileDialog(
            parent=self,
            caption="Browse files to publish"
        )
        file_dialog.setLabelText(QtGui.QFileDialog.Accept, "Select")
        file_dialog.setLabelText(QtGui.QFileDialog.Reject, "Cancel")
        file_dialog.setOption(QtGui.QFileDialog.DontResolveSymlinks)
        file_dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)
        file_dialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        if not file_dialog.exec_():
            return

        files = file_dialog.selectedFiles()
        # print files

        """Adds info to main_struct """
        self.main_struct[:] = []
        for f in files:
            f_path, f_name = os.path.split(f)
            tag_list = []
            tag_list.append(os.path.basename(f_path))
            self.main_struct.append(
                self.create_main_struct_entry(os.path.splitext(f_name)[0], str(self._combo_entity_type.currentText()),
                                              os.path.basename(f_path), tag_list, f_path, f_name, None))
            # PrettyPrinter(indent=4).pprint(self.main_struct)
            self._lbl_display_folder.setText(f_path)
        return True

    def create_version(self, temp_dict):
        """
        creates a single version. 
        TODO, optimize for multi project
        """
        data = {'project': {'type': 'Project', 'id': self.PROJECT_ID},
                'code': temp_dict['FileName'],
                'description': 'Test',
                # 'name': "015_Electricity.mov",
                'sg_status_list': 'na',
                'entity': {'type': 'Asset', 'id': temp_dict['id']},
                # 'sg_task': {'type': 'Task', 'id': task['id']},
                'user': {'type': 'HumanUser', 'id': 133},
                'sg_path_to_movie': os.path.join(temp_dict['FilePath'], temp_dict['FileName'])
                }
        PrettyPrinter(indent=4).pprint(data)
        return sg.create('Version', data)

    def create_publish(self, temp_dict):
        """
        creates a single publish. 
        TODO, publish_file_type needs to be dynamic
        TODO, optimize for multi project
        TODO, version_number needs to check shotgun for highest version number 
        TODO, change / to \\ before getting set into the main struct
        """
        data = {
            'project': {'type': 'Project', 'id': self.PROJECT_ID},
            'code': temp_dict['FileName'],
            'name': temp_dict['FileName'],
            # 'cached_display_name': os.path.splitext(t['FileName']),
            'published_file_type': {'id': 11, 'name': 'Movie', 'type': 'PublishedFileType'},
            'task': {'id': 9791, 'name': 'Publish', 'type': 'Task'},
            'path': {'content_type': 'video/quicktime',
                     'link_type': 'local',
                     'local_path': os.path.join(temp_dict['FilePath'], temp_dict['FileName']).replace("/", "\\"),
                     'local_path_linux': None,
                     'local_path_mac': None,
                     'local_path_windows': os.path.join(temp_dict['FilePath'], temp_dict['FileName']).replace("/",
                                                                                                              "\\"),
                     'local_storage': {'id': 2,
                                       'name': 'primary',
                                       'type': 'LocalStorage'},
                     'name': temp_dict['FileName'],
                     'type': 'Attachment',
                     'url': os.path.join(temp_dict['FilePath'], temp_dict['FileName'])},
            # 'path_cache': '	Library/Stock/Comp_Toolkit_2/DISC_10_Paint_Electricity/011_Electricity.mov',
            'version_number': 1
        }
        return sg.create('PublishedFile', data)

    def create_tag(self):
        """
        Creates tag on shotgun
        If tag exist, skip
        """
        filters = [['id', 'greater_than', 0]]
        # fields = ['name', 'task_template', 'updated_by']
        fields = ['name']
        temp_tag_list = sg.find('Tag', filters, fields)
        tag_list = []

        format_tag_list = self._txt_asset_tag.text().split(",")
        input_tag_list = []
        for l in format_tag_list:
            input_tag_list.append(l.strip())
        # print input_tag_list
        result = []
        for t in temp_tag_list:
            tag_list.append(t['name'])

        for input_tag in input_tag_list:
            if input_tag in tag_list:
                # print"Found Tag!!!"
                logger.info("Found Tag...")
                result.extend(sg.find('Tag', [['name', 'is', input_tag]], fields))
            else:
                # print "Creating Tag"
                logger.info("Creating Tag...")
                self.update_main_struct()
                self.create_tag_entry(input_tag)
                result.extend(sg.find('Tag', [['name', 'is', input_tag]], fields))
                # print "The id of the %s is %d." % (result[0]['type'], result['id'])
        # logger.info(result)
        return result

    def create_parent_asset(self, tag_list):
        """
        create parent asset with new/existing tags
        TODO,change to create 1 tag at a time instead of list. 
        """

        filters = [['id', 'greater_than', 0]]
        fields = ['cached_display_name']
        temp_asset_list = sg.find('Asset', filters, fields)
        # PrettyPrinter(indent=4).pprint(sg.find('Asset', filters, fields))

        asset_list = []
        for t in temp_asset_list:
            asset_list.append(t['cached_display_name'])

        result = []
        if self._txt_parent_assets.text() in asset_list:
            # print "Found Asset!!!"
            logger.info('Found Parent Assets...')
            result.extend(
                sg.find('Asset', [['cached_display_name', 'is', self.main_struct[0]['Info']['Parent Asset']]], fields))
            # return sg.find('Asset', [['cached_display_name', 'is', self._txt_parent_assets.text()]], fields)
        else:
            logger.info('Creating Parent Assets...')
            # print "Creating Asset"
            self.update_main_struct()
            # ---create parent asset
            self.create_asset_entry(self.main_struct[0]['Info']['Parent Asset'], "Parent Asset", "wtg",
                                    self._combo_entity_type.currentText(), tag_list, None)
            result.extend(
                sg.find('Asset', [['cached_display_name', 'is', self.main_struct[0]['Info']['Parent Asset']]], fields))

            # for t in tag_list:
            #     print "The id of the %s is %d." % (t['type'], t['id'])
        # logger.info(result)
        return result

    def create_child_asset(self, tag_list, parent_asset):
        """
        create child asset with linker to parent 
        #TODO change to 1 asset at a time. 
        """
        # filters = [['id', 'is', 1638]]
        # fields = ['cached_display_name', 'task_template', 'sg_asset_type', 'tag', 'parents']
        # PrettyPrinter(indent=4).pprint(sg.find('Asset', filters, fields))

        for t in self.main_struct:
            result = self.create_asset_entry(t['Info']['Asset Name'], "Child Asset", "wtg",
                                             self._combo_entity_type.currentText(),
                                             tag_list,
                                             parent_asset)
            t['id'] = result['id']
            # [{'id': 226, 'name': 'Hit', 'type': 'Tag'}],
            # [{'id': 1637, 'name': 'Dirt_Charges', 'type': 'Asset'}])

            logger.info('Creating Child Assets...')
            # print result

    def update_main_struct(self):
        """
        Update struct with new text 
        """
        # temp_list = self.main_struct
        for d in self.main_struct:
            d['Info']['Parent Asset'] = self._txt_parent_assets.text()
            d['Info']['Type'] = self._combo_entity_type.currentText()
            d['Info']['Tags'] = self._txt_asset_tag.text()

    def update_labels(self):

        temp_type = self.main_struct[0]['Info']['Type']
        temp_parent_asset = self.main_struct[0]['Info']['Parent Asset']
        temp_tag_txt = self.main_struct[0]['Info']['Tags']

        # self.txt_type.setText(temp_type)
        self._txt_parent_assets.setText(temp_parent_asset)
        self._txt_asset_tag.setText(','.join(map(str, temp_tag_txt)))

    def create_main_struct_entry(self, name, type, parent_asset, tag_list, f_path, f_name, id):
        """
        Main dict entry to store a single entry
        """
        return {'Info': {'Asset Name': name, 'Type': type, 'Task Template': "Library Asset",
                         'Parent Asset': parent_asset, 'Project': "Library", "Tags": tag_list}, 'FilePath': f_path,
                'FileName': f_name, 'id': id}

    def create_asset_entry(self, asset_name, asset_description, asset_status, asset_type, asset_tag, asset_parent):
        """
        Create a single shotgun asset entry 
        """
        # data = {
        #     'project': {"type": "Project", "id": 88},
        #     'code': asset_name,
        #     'description': 'Open on a beautiful field with fuzzy bunnies',
        #     'sg_status_list': 'ip',
        #     'sg_asset_type': 'Stock Footage',
        #     'tags': [{'id': 227, 'name': 'Couch', 'type': 'Tag'}],
        #     'task_template': {'id': 44, 'name': 'Library Asset', 'type': 'TaskTemplate'}
        # }

        if asset_parent is None:
            data = {
                'project': {"type": "Project", "id": self.PROJECT_ID},
                'code': asset_name,
                'description': asset_description,
                'sg_status_list': asset_status,
                'sg_asset_type': asset_type,
                'tags': asset_tag,
                'task_template': {'id': 44, 'name': 'Library Asset', 'type': 'TaskTemplate'},
            }
            result = sg.create('Asset', data)
        else:
            data = {
                'project': {"type": "Project", "id": self.PROJECT_ID},
                'code': asset_name,
                'description': asset_description,
                'sg_status_list': asset_status,
                'sg_asset_type': asset_type,
                'tags': asset_tag,
                'task_template': {'id': 44, 'name': 'Library Asset', 'type': 'TaskTemplate'},
                'parents': asset_parent
            }
            result = sg.create('Asset', data)
        return result

    def create_tag_entry(self, tag_name):
        """
        Create a single shotgun tag entry 
        """
        data = {
            'name': tag_name,
            'updated_by': {'id': 133, 'name': 'Johnny Zhu', 'type': 'HumanUser'}
        }
        result = sg.create('Tag', data)
        return result

    def create_main_struct_folder(self):
        """
        Select folder for publish
        """
        self.main_struct[:] = []
        # my_path = r'V:\projects\Library\Stock\Action_Essentials_2K\04. Couch_Hits'
        my_path = r'V:\projects\Library\Stock\Action_Essentials_2K\05. Debris'

        tag_list = []
        for (dir_path, dir_names, file_names) in walk(my_path):
            # dir_names.sort()
            file_names.sort()

            temp_path = dir_path.replace(os.path.dirname(my_path), "")

            # tag_list = temp_path.split(os.sep)
            tag_list.append(os.path.basename(dir_path))
            for f in file_names:
                self.main_struct.append(
                    self.create_main_struct_entry(os.path.splitext(f)[0], str(self._combo_entity_type.currentText()),
                                                  os.path.basename(dir_path), tag_list))

    def _test_create_tag(self):
        """
        TESTING
        """
        # filters = [['id', 'is', 227]]
        # fields = ['name','task_template','updated_by']
        # PrettyPrinter(indent=4).pprint(sg.find('Tag', filters,fields))

        data = {
            # 'project': {"type": "Project", "id": 88},
            'name': 'Fluffy Unicorn',
            'updated_by': {'id': 133, 'name': 'Johnny Zhu', 'type': 'HumanUser'}
        }

        result = sg.create('Tag', data)
        print "The id of the %s is %d." % (result['type'], result['id'])

    def _test_create_asset(self):
        """
        TESTING
        """
        # filters = [['id', 'is', 1604]]
        # fields = ['cached_display_name','task_template','sg_asset_type','tags']
        # PrettyPrinter(indent=4).pprint(sg.find('Asset', filters,fields))

        data = {
            'project': {"type": "Project", "id": 88},
            'code': 'Fluffy Unicorn',
            'description': 'Open on a beautiful field with fuzzy bunnies',
            'sg_status_list': 'ip',
            'sg_asset_type': 'Stock Footage',
            'tags': ['Debris'],
            'task_template': {'id': 44, 'name': 'Library Asset', 'type': 'TaskTemplate'}
        }
        result = sg.create('Asset', data)
        print "The id of the %s is %d." % (result['type'], result['id'])

    def _test_create_version(self):
        """
        TESTING
        """
        data = {'project': {'type': 'Project', 'id': self.PROJECT_ID},
                'code': '011_Electricity.mov',
                'description': 'first pass at opening shot with bunnies',
                # 'name': "015_Electricity.mov",
                # 'sg_path_to_movie': r'V:\projects\Library\Stock\Action_Essentials_2K\05. Debris\Debris_Fall_05.mov',
                'sg_status_list': 'na',
                'entity': {'type': 'Asset', 'id': 1982},
                # 'sg_task': {'type': 'Task', 'id': task['id']},
                'user': {'type': 'HumanUser', 'id': 133},
                'sg_path_to_movie': r'V:\projects\Library\Stock\Comp_Toolkit_2\DISC_10_Paint_Electricity\011_Electricity.mov'
                }

        return sg.create('Version', data)
        # print result

    def _test_create_publish(self):
        """
        TESTING
        """

        data = {
            'project': {'type': 'Project', 'id': 88},
            'code': '011_Electricity.mov',
            'name': '011_Electricity.mov',
            'cached_display_name': "011_Electricity",
            'published_file_type': {'id': 11, 'name': 'Movie', 'type': 'PublishedFileType'},
            'task': {'id': 9791, 'name': 'Publish', 'type': 'Task'},
            'path': {'content_type': 'video/quicktime',
                     'link_type': 'local',
                     'local_path': r'V:\projects\Library\Stock\Comp_Toolkit_2\DISC_10_Paint_Electricity\011_Electricity.mov',
                     'local_path_linux': None,
                     'local_path_mac': None,
                     'local_path_windows': r'V:\projects\Library\Stock\Comp_Toolkit_2\DISC_10_Paint_Electricity\011_Electricity.mov',
                     'local_storage': {'id': 2,
                                       'name': 'primary',
                                       'type': 'LocalStorage'},
                     'name': '011_Electricity.mov',
                     'type': 'Attachment',
                     'url': r'file:/V:\projects\Library\Stock\Comp_Toolkit_2\DISC_10_Paint_Electricity\011_Electricity.mov'},
            'path_cache': '	Library/Stock/Comp_Toolkit_2/DISC_10_Paint_Electricity/011_Electricity.mov',
            'version_number': 1
        }

        return sg.create('PublishedFile', data)


class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super(QPlainTextEditLogger, self).__init__()

        self.widget = QtGui.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

    def write(self, m):
        pass


class Completer_new(QtGui.QCompleter):
    """
    Wrapper for QCompleter
    Seperates by commas
    """

    def __init__(self, parent=None):
        QtGui.QCompleter.__init__(self, parent)

    def pathFromIndex(self, index):
        path = QtGui.QCompleter.pathFromIndex(self, index)

        word_list = str(self.widget().text()).split(',')
        # print word_list
        if len(word_list) > 1:
            # print "word_list", word_list[:-1]
            path = '%s, %s' % (','.join(word_list[:-1]), path)
        # print path
        return path

    def splitPath(self, path):
        path = str(path.split(',')[-1]).strip(' ')
        # print path
        return [path]
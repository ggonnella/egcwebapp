import os
import hashlib
import shutil
from egctools.egctools import unparsed_and_parsed_lines, encode_line
from collections import defaultdict

class EGCData:
    def __init__(self, file_path, records = [], lines = [],
                 id2record = {}, docid2record = {},
                 record_type2records = defaultdict(list)):
        self.file_path = file_path
        self.records = records
        self.lines = lines
        self.id2record = id2record
        self.docid2record = docid2record
        self.record_type2records = record_type2records

    @classmethod
    def from_file(cls, file_path, backup=False):
        if not os.path.exists(file_path):
          raise FileNotFoundError('File not found: {}'.format(file_path))
        id2record = {}
        docid2record = {}
        record_type2records = defaultdict(list)
        records = []
        lines = []
        for unparsed, parsed in unparsed_and_parsed_lines(file_path):
          lines.append(unparsed)
          records.append(parsed)
          record_type2records[parsed['record_type']].append(len(records) - 1)
          if 'id' in parsed:
            id2record[parsed['id']] = len(records) - 1
          if parsed['record_type'] == 'D':
            docid2record[parsed['document_id']['item']] = len(records) - 1
        if backup:
          backup_file_path = EGCData._get_backup_file_path(file_path)
          if not os.path.exists(backup_file_path):
            shutil.copyfile(file_path, backup_file_path)
        return cls(file_path, records, lines, id2record, docid2record,
            record_type2records)

    @staticmethod
    def _get_backup_file_path(file_path, prefix_length=8):
      # Calculate the hash of the original file content
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
          hasher.update(f.read())
        hash_prefix = hasher.hexdigest()[:prefix_length]

        # Construct the backup file path
        backup_file_path = f"{file_path}.{hash_prefix}.bak"
        return backup_file_path

    def save_data(self, backup=False):
        if backup:
          backup_file_path = EGCData._get_backup_file_path(self.file_path)
          if not os.path.exists(backup_file_path):
            shutil.copyfile(self.file_path, backup_file_path)

        with open(self.file_path, 'w') as f:
          for line in self.lines:
            if line is not None:
              f.write(line + "\n")

    def get_documents(self):
      return [self.records[i] for i in self.record_type2records['D']]

    def get_document(self, record_id):
      record_num = self.docid2record[record_id]
      if record_num is None:
        raise ValueError('Document does not exist: {}'.format(record_id))
      return self.records[record_num]

    def create_record(self, record_data, id_key, id_map):
        if isinstance(id_key, str):
          id_key = [id_key]
        record_id = record_data[id_key.pop(0)]
        while len(id_key) > 0:
          record_id = record_id[id_key.pop(0)]
        if record_id in id_map:
            raise ValueError('Record already exists: {}'.format(record_id))
        self.records.append(record_data)
        self.lines.append(encode_line(record_data))
        record_num = len(self.records) - 1
        id_map[record_id] = record_num
        record_type = record_data["record_type"]
        self.record_type2records[record_type].append(record_num)
        self.save_data()

    def create_document(self, document_data):
      self.create_record(document_data, ['document_id', 'item'],
          self.docid2record)

    def create_record_with_id(self, record_data):
      self.create_record(record_data, 'id', self.id2record)

    def delete_record(self, record_id, id_map):
      if record_id not in id_map:
          raise ValueError('Record does not exist: {}'.format(record_id))
      record_num = id_map[record_id]
      record_type = self.records[record_num]["record_type"]
      self.record_type2records[record_type].remove(record_num)
      self.records[record_num] = None
      self.lines[record_num] = None
      del id_map[record_id]
      self.save_data()

    def delete_document(self, document_id):
      self.delete_record(document_id, self.docid2record)

    def delete_record_by_id(self, record_id):
      self.delete_record(record_id, self.id2record)

    def update_record(self, record_id, id_key, id_map, updated_data):
      if record_id not in id_map:
          raise ValueError('Record does not exist: {}'.format(record_id))
      record_num = id_map[record_id]
      if isinstance(id_key, str):
        id_key = [id_key]
      updated_id = updated_data[id_key.pop(0)]
      while len(id_key) > 0:
        updated_id = updated_id[id_key.pop(0)]
      if updated_id != record_id:
          if updated_id in id_map:
              raise ValueError('Record already exists: {}'.format(updated_id))
          id_map[updated_id] = record_num
          del id_map[record_id]
      self.records[record_num] = updated_data
      self.lines[record_num] = encode_line(updated_data)
      self.save_data()

    def update_document(self, document_id, updated_data):
      self.update_record(document_id, ['document_id', 'item'],
            self.docid2record, updated_data)

    def update_record_by_id(self, record_id, updated_data):
      self.update_record(record_id, 'id', self.id2record, updated_data)

    def is_unique_document(self, document_id):
      return document_id not in self.docid2record

    def get_snippets_and_tables(self):
      return [self.records[i] for i in self.record_type2records['S']] + \
             [self.records[i] for i in self.record_type2records['T']]

    def get_snippet_table(self, record_id):
      record_num = self.id2record[record_id]
      if record_num is None:
        raise ValueError('Record does not exist: {}'.format(record_id))
      return self.records[record_num]

    def create_snippet_table(self, record_data):
      self.create_record_with_id(record_data)

    def update_snippet_table(self, record_id, updated_data):
      self.update_record_by_id(record_id, updated_data)

    def delete_snippet_table(self, record_id):
      self.delete_record_by_id(record_id)

    def is_unique_id(self, record_id):
      return record_id not in self.id2record

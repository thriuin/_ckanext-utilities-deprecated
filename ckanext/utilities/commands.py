from ckan.lib.cli import CkanCommand
import ckanapi
from ckanext.canada.metadata_schema import schema_description
import csv
from paste.script import command

__author__ = 'thomros'


class UtilCommand(CkanCommand):
    """
        CKAN Utilities Extension

        Usage::

            paster canada org_datasets  -g <organization> [-r <remote server>] ][-c <configuration file>]
                          del_datasets  -f <source_file> [-a <apikey>] [-r <remote server>] [-c <configuration file>]
                          report_raw_datasets -f <source_file> [-r <remote server>] ][-c <configuration file>]
        Options::

            -a/--apikey <apikey>                push to <remote server> using apikey
            -g/--org <organization>             Organizations ID e.g. ec
            -f/--file <src_file>                Text file. For del_datasets this is list of package ID's.
                                                For report_raw_datasets this is the CSV file that is generated.
            -r/--remote_server <remote server>  Remote CKAN server to connect to. Default: "localhost"
            -c/--config <configuration file>    Paster configuration file

        Examples::

            paster ckan_util extract_datasets -f myreport.csv -r http://open.data.org/data/

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = command.Command.standard_parser(verbose=True)

    parser.add_option('-a', '--apikey', dest='apikey', default=None)
    parser.add_option('-r', '--remote_server', dest='remote', default='localhost')
    parser.add_option('-g', '--org', dest='organization', default='*')
    parser.add_option('-f', '--file', dest='src_file', default='')
    parser.add_option('-c', '--config', dest='config',
        default='development.ini', help='Configuration file to use.')

    res_types = schema_description.resource_field_by_id['resource_type']['choices_by_key']
    langs = schema_description.resource_field_by_id['language']['choices_by_key']
    fmt = schema_description.resource_field_by_id['format']['choices_by_key']

    def command(self):
      '''
      Parse command line arguments and call appropriate method.
      '''
      if not self.args or self.args[0] in ['--help', '-h', 'help']:
          print self.__doc__
          return

      cmd = self.args[0]

      self._load_config()

      ckan_server = None
      if self.options.remote <> 'localhost':
        ckan_server = ckanapi.RemoteCKAN(self.options.remote)
      else:
        ckan_server = ckanapi.LocalCKAN()

      if cmd == 'org_datasets':
        org_query = "organization:%s" % self.options.organization
        result = ckan_server.action.package_search(fq=org_query, rows='100')
        # data.gc.ca imposes a limit of 100 rows returned at a time. This could be made more dynamic to handle
        # arbitrary row limits used by other sites.
        count = result['count']
        for ds in result['results']:
          print ds['name']
        if count > 100:
          start_row = 100
          while count > 0:
             result = ckan_server.action.package_search(fq=org_query, rows='100', start=start_row)
             for ds in result['results']:
               print ds['name']
             start_row += 100
             count -= 100

      elif cmd == 'del_datasets':

        id_list = []
        f = open(self.options.src_file)
        id_list = f.readlines()
        f.close()
        for id in id_list:
          print "Deleting Package %s" % id.strip()
          ckan_server.action.package_delete(id=id.strip())

      elif cmd == 'report_raw_datasets':
        # Write out a CSV file with some basic information about raw data-sets

        ds_query = "catalog_type:\"Data | Donn\u00e9es\""
        result = ckan_server.action.package_search(fq=ds_query, rows='100')
        count = result['count']
        print "%s records found" % count

        csvfile = open(self.options.src_file, 'wb')
        csvwriter = csv.writer(csvfile, dialect='excel')

        # Create the header
        header_fields = ['ID', 'Title English','Title French','Publisher','Data Type','Openness Score']
        i = 0
        while i < 12:
          i += 1
          header_fields.extend(['Format','Type','Title English','Title French','URL',	'Language'])
        csvwriter.writerow(header_fields)

        self._extract_lines(result['results'], csvwriter)
        if count > 100:
          start_row = 100
          while count > 0:
            result = ckan_server.action.package_search(fq=ds_query, rows='100', start=start_row)
            self._extract_lines(result['results'], csvwriter)
            start_row += 100
            count -= 100

        csvfile.close()


    def _get_extra_field(self, package_dict, field_name):
      rc = ""
      for field in package_dict['extras']:
        if field['key'] == field_name:
          rc = field['value']
      return rc

    def _encode_fields(self, fields):
      ufields = []
      for field in fields:
        if field:
          field = field.split('|')[0]
          ufields.append(field.encode('cp1252'))
        else:
          ufields.append(field)
      return ufields

    def _openness_score(self, res_dict):
      score = 0
      for r in res_dict:
          if r['resource_type'] != 'file':
              continue
          score = max(score, self.fmt[r['format']]['openness_score'])
      return score.__str__()

    def _extract_lines(self, datasets, csvwriter):
      for ds in datasets:
        fields = [ds['id'], ds['title'], ds['title_fra'], ds['organization']['title']]
        fields.append(self._get_extra_field(ds, 'catalog_type'))
        fields.append(self._openness_score(ds['resources']))

        for rs in ds['resources']:
          fields.extend([rs['format'],
                         self.res_types[rs['resource_type']]['eng'],
                         rs['name'],rs['name_fra'],
                         rs['url'],
                         self.langs[rs['language']]['eng']])
        csvwriter.writerow(self._encode_fields(fields))
        print ds['name']
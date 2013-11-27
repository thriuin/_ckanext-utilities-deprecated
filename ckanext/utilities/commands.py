from ckan.lib.cli import CkanCommand
import ckanapi
from ckanext.canada.metadata_schema import schema_description
import csv
from paste.script import command
import org_commands

__author__ = 'Statistics Canada'
__copyright__ = "Copyright 2013, Government of Canada"
__maintainer__ = "Ross Thompson"
__license__ = "MIT"
__status__ = "Development"

class UtilCommand(CkanCommand):
    """CKAN Utilities Extension

        Usage::

            paster utility org-datasets  -i <organization> [-r <remote server>] ][-c <configuration file>]
                           move-org-datasets -1 <organization> -2 <organization> [-r <remote server>] ]
                                [-c <configuration file>][-v]
                           delete-org -i <organization>
                           del-datasets  -f <source_file> [-a <apikey>] [-r <remote server>] [-c <configuration file>]
                           report-raw-datasets -f <source_file> [-r <remote server>] ][-c <configuration file>]
        Options::

            -1/--org_from <organization>        From Organization ID
            -2/--org_to <organization>          To Organization ID
            -a/--apikey <apikey>                push to <remote server> using apikey
            -c/--config <configuration file>    Paster configuration file
            -f/--file <src_file>                Text file. For del_datasets this is list of package ID's.
                                                For report_raw_datasets this is the CSV file that is generated.
            -i/--org <organization>             Organization ID e.g. ec
            -r/--remote_server <remote server>  Remote CKAN server to connect to. Default: "localhost"
                                                Be sure to use the prefix in the server name e.g. http://data.gc.ca
            -v/--verbose                        Display status messages while processing command

        Examples::

            paster ckan_util report_raw_datasets -f myreport.csv -r http://open.data.org/data/

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = command.Command.standard_parser(verbose=True)

    parser.add_option('-a', '--apikey', dest='apikey', default=None)
    parser.add_option('-r', '--remote_server', dest='remote', default='localhost')
    parser.add_option('-i', '--org', dest='organization', default='*')
    parser.add_option('-1', '--org_from', dest='org_from', default=None)
    parser.add_option('-2', '--org_to', dest='org_to', default=None)
    parser.add_option('-f', '--file', dest='src_file', default='')
    parser.add_option('-c', '--config', dest='config',
                      default='development.ini', help='Configuration file to use.')
    parser.add_option('-G', '--geo', dest='geo_only', action='store_true')


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
            if self.options.apikey:
                ckan_server = ckanapi.RemoteCKAN(self.options.remote, apikey=self.options.apikey)
            else:
                ckan_server = ckanapi.RemoteCKAN(self.options.remote)
        else:
            ckan_server = ckanapi.LocalCKAN()

        # Organization Commands

        org_commands.cmd_configure(ckan_server)
        if cmd == 'org-datasets':

            if self.options.geo_only:
                org_commands.get_datasets(self.options.organization, u"Geo Data | G\u00e9o")
            else:
                org_commands.get_datasets(self.options.organization)

        elif cmd == 'move-org-datasets':
            if self.options.org_from and self.options.org_to:
                org_commands.move_datasets(self.options.org_from, self.options.org_to, self.options.verbose)
            else:
                print self.usage

        elif cmd == 'delete-org':
            if self.options.organization == '*':
                print "Please provide a valid organization ID"
            else:
                org_commands.delete_organization(self.options.organization)

        elif cmd == 'del-datasets':

            id_list = []
            f = open(self.options.src_file)
            id_list = f.readlines()
            f.close()
            for id in id_list:
                print "Deleting Package %s" % id.strip()
                ckan_server.action.package_delete(id=id.strip())

        elif cmd == 'report-raw-datasets':
        # Write out a CSV file with some basic information about raw data-sets

            ds_query = "catalog_type:\"Data | Donn\u00e9es\""
            result = ckan_server.action.package_search(fq=ds_query, rows='100')
            count = result['count']
            print "%s records found" % count

            csvfile = open(self.options.src_file, 'wb')
            csvwriter = csv.writer(csvfile, dialect='excel')

            # Create the header
            header_fields = ['ID', 'Title English', 'Title French', 'Publisher', 'Data Type', 'Openness Score']
            i = 0
            while i < 12:
                i += 1
                header_fields.extend(['Format', 'Type', 'Title English', 'Title French', 'URL', 'Language'])
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
                               rs['name'], rs['name_fra'],
                               rs['url'],
                               self.langs[rs['language']]['eng']])
            csvwriter.writerow(self._encode_fields(fields))
            print ds['name']
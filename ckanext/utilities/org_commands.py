from ckan.logic import NotFound
from ckan.logic.validators import isodate, boolean_validator
from ckanext.canada.metadata_schema import schema_description
from ckanext.canada.navl_schema import convert_pilot_uuid_list
from ckan.lib.navl.dictization_functions import Invalid

__author__ = 'Ross Thompson'

_ckan_server = None
_rows = 100

def cmd_configure(ckan_server, rows=100):
    """Set up the CKAN server query object"""

    global _ckan_server, _rows
    _ckan_server = ckan_server
    _rows = rows

def get_datasets(organization, catalog_type = None):
    """Get a list of dataset IDs that belong to a specific organization."""

    global _ckan_server, _rows

    org_query = "organization:%s" % organization
    if catalog_type:
        org_query = "organization:%s AND catalog_type:\"%s\"" % (organization, catalog_type)
    result = _ckan_server.action.package_search(fq=org_query, rows='%s' % _rows)
    # data.gc.ca imposes a limit of 100 rows returned at a time. This could be made more dynamic to handle
    # arbitrary row limits used by other sites.
    count = result['count']
    for ds in result['results']:
        print ds['name']
    if count > _rows:
        start_row = _rows
        while count > 0:
            result = _ckan_server.action.package_search(fq=org_query, rows='%s' % _rows, start=start_row)
            for ds in result['results']:
                print ds['name']
            start_row += _rows
            count -= _rows

def move_datasets(org_from, org_to, verbose=False):
    """Move all the datasets from one organization to another."""

    global _ckan_server, _rows

    # Validate that org_to actually exists

    try:
        result = _ckan_server.action.organization_show(id=org_to)
    except NotFound, e:
        print "Cannot find organization: %s" % org_to
        return

    # Get all packages for the organization then update each dataset

    org_query = "organization:%s" % org_from
    result = _ckan_server.action.package_search(fq=org_query, rows='%s' % _rows)
    for ds in result['results']:
        package = _ckan_server.action.package_show(id=ds['id'])
        package['owner_org'] = org_to
        _ckan_server.action.package_update(**package)
        if verbose:
            print "Moved %s" % ds['id']


# -*- coding: utf-8 -*-

from flask import render_template, Response

import conf
from pyldapi import Renderer, Profile
from rdflib import Graph, URIRef, RDF, Namespace, Literal, BNode
from rdflib.namespace import XSD   #imported for 'export_rdf' function

from .gazetteer import GAZETTEERS, NAME_AUTHORITIES
from .dggs_in_line import get_cells_in_json_and_return_in_json

# for DGGSC:C zone attribution
import requests
import ast
DGGS_API_URI = "http://ec2-3-26-44-145.ap-southeast-2.compute.amazonaws.com/api/search/"
test_DGGS_API_URI = "https://dggs.loci.cat/api/search/"
DGGS_uri = 'http://ec2-52-63-73-113.ap-southeast-2.compute.amazonaws.com/AusPIX-DGGS-dataset/ausPIX/'

from rhealpixdggs import dggs
rdggs = dggs.RHEALPixDGGS()


class Power_substation(Renderer):
    """
    This class represents a placename and methods in this class allow a placename to be loaded from the GA placenames
    database and to be exported in a number of formats including RDF, according to the 'PlaceNames Ontology'

    [[and an expression of the Dublin Core ontology, HTML, XML in the form according to the AS4590 XML schema.]]??
    """

    def __init__(self, request, uri):
        format_list = ['text/html', 'text/turtle', 'application/ld+json', 'application/rdf+xml']
        views = {
            'Power substation': Profile(
                'http://linked.data.gov.au/def/power/',
                'Power Station View',
                'This view is for power station delivered by the power sub station dataset'
                ' in accordance with the Power Station Profile',
                format_list,
                'text/html'
            )
        }

        super(Power_substation, self).__init__(request, uri, views, 'Power substation')

        self.id = uri.split('/')[-1]

        self.hasName = {
            'uri': 'http://linked.data.gov.au/def/power/',
            'label': 'Power substation:',
            'comment': 'The Entity has a name (label) which is a text string.',
            'value': None
        }

        self.thisCell = {
            'label': None,
            'uri': None
        }

        # self.uri = None
        # self.feature_type = None
        # self.operational_status = None
        # self.custodian_agency = None
        # self.physical_condition = None
        # self.power_source = None
        # self.substation_class = None
        # self.structuretype = None
        # self.voltage = None
        # self.address = None
        # self.textnote = None
        # self.wkt = None


        q = '''
            SELECT
                "name",
                "uri",
                "feature_type",
                "operational_status",
                "custodian_agency",
                "physical_condition",
                "power_source",
                "class",
                "structuretype",
                "voltage",
                "address",
                "textnote",
                "feature_date",
                "feature_source",
                "attribute_date",
                "attribute_source",
                "vertical_accuracy",
                "planimetric_accuracy",
                "source_ufi",
                "source_jurisdiction",                                
                "custodian_licensing",
                "loading_date",
                ST_AsEWKT(geom) As geom_wkt,                
                ST_AsGeoJSON(geom) As geom
            FROM "power_substation_points84"
            WHERE "id" = '{}'
        '''.format(self.id)

        for row in conf.db_select(q):
            self.hasName['value'] = str(row[0])
            self.uri = row[1]
            self.feature_type = row[2]
            self.operational_status = row[3]
            self.custodian_agency = row[4]
            self.physical_condition = row[5]
            self.power_source = row[6]
            self.substation_class = row[7]
            self.structuretype = row[8]
            self.voltage = row[9]
            self.address = row[10]
            self.textnote = row[11]
            self.feature_date = row[12]
            self.feature_source = row[13]
            self.attribute_date = row[14]
            self.attribute_source = row[15]
            self.vertical_accuracy = row[16]
            self.planimetric_accuracy = row[17]
            self.source_ufi = row[18]
            self.source_jurisdiction = row[19]
            self.custodian_licensing = row[20]
            self.loading_date = row[21]

            # get geometry from database
            self.geom = ast.literal_eval(row[-1])
            self.coords = self.geom['coordinates']
            self.wkt = row[-2]

            DGGS_uri = 'http://ec2-52-63-73-113.ap-southeast-2.compute.amazonaws.com/AusPIX-DGGS-dataset/ausPIX/'
            resolution = 11
            coords = (self.coords[0], self.coords[1])
            self.thisDGGSCell = rdggs.cell_from_point(resolution, coords,
                                                      plane=False)  # false = on the elipsoidal curve
            self.thisCell['label'] = str(self.thisDGGSCell)
            self.thisCell['uri'] = '{}{}'.format(DGGS_uri, str(self.thisDGGSCell))



    def render(self):
        if self.profile == 'alt':
            return self._render_alt_profile()  # this function is in Renderer
        elif self.mediatype in ['text/turtle', 'application/ld+json', 'application/rdf+xml']:
            return self.export_rdf(self.profile)
        else:  # default is HTML response: self.format == 'text/html':
            return self.export_html(self.profile)


    def export_html(self, model_view='Power_substation'):
        html_page = 'power_substation.html'
        return Response(        # Response is a Flask class imported at the top of this script
            render_template(     # render_template is also a Flask module
                html_page,   # uses the html template to send all this data to it.
                id=self.id,
                hasName=self.hasName,
                feature_type=self.feature_type,
                operational_status=self.operational_status,
                custodian_agency=self.custodian_agency,
                physical_condition=self.physical_condition,
                power_source=self.power_source,
                substation_class=self.substation_class,
                structuretype=self.structuretype,
                voltage=self.voltage,
                address=self.address,
                textnote=self.textnote,
                feature_date=self.feature_date,
                feature_source=self.feature_source,
                attribute_date=self.attribute_date,
                attribute_source=self.attribute_source,
                vertical_accuracy=self.vertical_accuracy,
                planimetric_accuracy=self.planimetric_accuracy,
                source_ufi=self.source_ufi,
                source_jurisdiction=self.source_jurisdiction,
                custodian_licensing=self.custodian_licensing,
                loading_date=self.loading_date,
                coordinate_list = self.coords,
                ausPIX_DGGS = self.thisCell,
                wkt = self.wkt
            ),
            status=200,
            mimetype='text/html'
        )


    # def _generate_wkt(self):
    #     """
    #     Polygon: 8
    #     Point: 6889
    #     :return:
    #     :rtype:
    #     """
    #     if self.geometry_type == 'Point':
    #         coordinates = {
    #             'srid': self.srid,
    #             'x': self.coords[0],
    #             'y': self.coords[1]
    #         }
    #         wkt = 'SRID={srid};POINT({x} {y})'.format(**coordinates)
    #     elif self.geometry_type == 'Polygon':
    #         start = 'SRID={srid};POLYGON(('.format(srid='WGS84')
    #         coordinates = ''
    #         for coord in zip(self.lons, self.lats):
    #             coordinates += '{} {},'.format(coord[0], coord[1])
    #
    #         coordinates = coordinates[:-1]  # drop the final ','
    #         end = '))'
    #         wkt = '{start}{coordinates}{end}'.format(start=start, coordinates=coordinates, end=end)
    #     else:
    #         wkt = ''
    #
    #     return wkt


    def _generate_wkt(self):
        if self.id is not None and self.x is not None and self.y is not None:
            return 'POINT({} {})'.format(self.y, self.x)
        else:
            return ''

    def _generate_dggs(self):
        if self.id is not None and self.thisCell is not None:
            return '{}'.format(self.thisCell)
        else:
            return ''


    def export_rdf(self, model_view='NCGA'):
        g = Graph()  # make instance of a RDF graph

        # namespace declarations
        dcterms = Namespace('http://purl.org/dc/terms/')  # already imported
        g.bind('dcterms', dcterms)
        geo = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geo', geo)
        owl = Namespace('http://www.w3.org/2002/07/owl#')
        g.bind('owl', owl)
        rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
        g.bind('rdfs', rdfs)

        # specific to placename datasdet
        place = Namespace('http://linked.data.gov.au/dataset/placenames/place/')
        g.bind('place', place)
        pname = URIRef('http://linked.data.gov.au/dataset/placenames/placenames/')
        g.bind('pname', pname)
        # made the cell ID the subject of the triples
        auspix = URIRef('http://ec2-52-63-73-113.ap-southeast-2.compute.amazonaws.com/AusPIX-DGGS-dataset/')
        g.bind('auspix', auspix)
        pn = Namespace('http://linked.data.gov.au/def/placenames/')
        g.bind('pno', pn)

        geox = Namespace('http://linked.data.gov.au/def/geox#')
        g.bind('geox', geox)
        g.bind('xsd', XSD)
        sf = Namespace('http://www.opengis.net/ont/sf#')
        g.bind('sf', sf)
        ptype = Namespace('http://pid.geoscience.gov.au/def/voc/ga/PlaceType/')
        g.bind('ptype', ptype)

        # build the graphs
        official_placename = URIRef('{}{}'.format(pname, self.id))
        this_place = URIRef('{}{}'.format(place, self.id))
        g.add((official_placename, RDF.type, URIRef(pn + 'OfficialPlaceName')))
        g.add((official_placename, dcterms.identifier, Literal(self.id, datatype=pn.ID_GAZ)))
        g.add((official_placename, dcterms.identifier, Literal(self.auth_id, datatype=pn.ID_AUTH)))
        g.add((official_placename, dcterms.issued, Literal(str(self.supplyDate), datatype=XSD.dateTime)))
        g.add((official_placename, pn.name, Literal(self.hasName['value'], lang='en-AU')))
        g.add((official_placename, pn.placeNameOf, this_place))
        g.add((official_placename, pn.wasNamedBy, URIRef(self.authority['web'])))
        g.add((official_placename, rdfs.label, Literal(self.hasName['value'])))

        # if NCGA view, add the place info as well
        if model_view == 'NCGA':
            g.add((this_place, RDF.type, URIRef(pn + 'Place')))
            g.add((this_place, dcterms.identifier, Literal(self.id, datatype=pn.ID_GAZ)))
            g.add((this_place, dcterms.identifier, Literal(self.auth_id, datatype=pn.ID_AUTH)))

            place_point = BNode()
            g.add((place_point, RDF.type, URIRef(sf + 'Point')))
            g.add((place_point, geo.asWKT, Literal(self._generate_wkt(), datatype=geo.wktLiteral)))
            g.add((this_place, geo.hasGeometry, place_point))

            place_dggs = BNode()
            g.add((place_dggs, RDF.type, URIRef(geo + 'Geometry')))
            g.add((place_dggs, geox.asDGGS, Literal(self._generate_dggs(), datatype=geox.dggsLiteral)))
            g.add((this_place, geo.hasGeometry, place_dggs))

            g.add((this_place, pn.hasPlaceClassification, URIRef(ptype + self.featureType['label'])))
            g.add((this_place, pn.hasPlaceClassification, URIRef(ptype + self.hasCategory['label'])))
            g.add((this_place, pn.hasPlaceClassification, URIRef(ptype + self.hasGroup['label'])))
            g.add((this_place, pn.hasPlaceName, official_placename))

        if self.mediatype == 'text/turtle':
            return Response(
                g.serialize(format='turtle'),
                mimetype = 'text/turtle'
            )
        elif self.mediatype == 'application/rdf+xml':
            return Response(
                g.serialize(format='application/rdf+xml'),
                mimetype = 'application/rdf+xml'
            )
        else: # JSON-LD
            return Response(
                g.serialize(format='json-ld'),
                mimetype = 'application/ld+json'
            )


if __name__ == '__main__':
    pass





# -*- coding: utf-8 -*-
from bms.v1.action import Action
from bms.v1.exceptions import (
    PatchAttributeException
)
from bms.v1.borehole.geom.patch import PatchGeom


class PatchBorehole(Action):

    async def execute(self, id, field, value, user_id):
        try:
            # Updating character varing field
            if field in [
                'extended.original_name',
                'custom.public_name',
                'custom.project_name',
                'custom.canton',
                'custom.city',
                'custom.address',
                'location_x',
                'location_y',
                'elevation_z',
                'canton',
                'address',
                'drill_diameter',
                'custom.drill_diameter',
                'bore_inc',
                'bore_inc_dir',
                'length',
                'extended.top_bedrock',
                'extended.groundwater'
                    ]:

                column = None

                if field == 'extended.original_name':
                    column = 'original_name_bho'

                if field == 'custom.public_name':
                    column = 'public_name_bho'

                if field == 'custom.project_name':
                    column = 'project_name_bho'

                if field == 'custom.address':
                    column = 'address_bho'

                elif field in ['location_x', 'location_y']:

                    geom = PatchGeom(self.conn)
                    await geom.execute(id, field, value)

                    if field == 'location_x':
                        column = 'location_x_bho'

                    elif field == 'location_y':
                        column = 'location_y_bho'

                elif field == 'elevation_z':
                    column = 'elevation_z_bho'

                if field == 'custom.canton':
                    column = 'canton_bho'

                if field == 'custom.city':
                    column = 'city_bho'

                elif field == 'canton':
                    column = 'canton_num'

                elif field == 'address':
                    column = 'address_bho'

                elif field == 'custom.drill_diameter':
                    column = 'drill_diameter_bho'

                elif field == 'bore_inc':
                    column = 'bore_inc_bho'

                elif field == 'bore_inc_dir':
                    column = 'bore_inc_dir_bho'

                elif field == 'length':
                    column = 'length_bho'

                elif field == 'extended.top_bedrock':
                    column = 'top_bedrock_bho'

                elif field == 'extended.groundwater':
                    column = 'groundwater_bho'

                await self.conn.execute("""
                    UPDATE public.borehole
                    SET %s = $1
                    WHERE id_bho = $2
                """ % column, value, id)

            # Datetime values
            elif field in [
                        'restriction_until',
                        'drilling_date'
                    ]:

                column = None

                if field == 'restriction_until':
                    column = 'restriction_until_bho'

                elif field == 'drilling_date':
                    column = 'drilling_date_bho'

                await self.conn.execute("""
                    UPDATE public.borehole
                    SET %s = to_date($1, 'YYYY-MM-DD')
                    WHERE id_bho = $2
                """ % column, value, id)

            elif field in [
                        'restriction',
                        'kind',
                        'srs',
                        'qt_location',
                        'qt_elevation',
                        'hrs',
                        'custom.landuse',
                        'extended.method',
                        'custom.cuttings',
                        'extended.purpose',
                        'extended.status',
                        'custom.qt_bore_inc_dir',
                        'custom.qt_length',
                        'custom.qt_top_bedrock'
                    ]:

                column = None

                # Check if domain is extracted from the correct schema
                schema = await self.conn.fetchval("""
                    SELECT
                        schema_cli
                    FROM
                        codelist
                    WHERE id_cli = $1
                """, value)

                if schema != field:
                    raise Exception(
                        "Attribute id %s not part of schema %s" %
                        (
                            value, field
                        )
                    )

                if field == 'restriction':
                    column = 'restriction_id_cli'

                elif field == 'kind':
                    column = 'kind_id_cli'

                elif field == 'srs':
                    column = 'srs_id_cli'

                elif field == 'qt_location':
                    column = 'qt_location_id_cli'

                elif field == 'qt_elevation':
                    column = 'qt_elevation_id_cli'

                elif field == 'hrs':
                    column = 'hrs_id_cli'

                elif field == 'custom.landuse':
                    column = 'landuse_id_cli'

                elif field == 'extended.method':
                    column = 'method_id_cli'

                elif field == 'custom.cuttings':
                    column = 'cuttings_id_cli'

                elif field == 'extended.purpose':
                    column = 'purpose_id_cli'

                elif field == 'extended.status':
                    column = 'status_id_cli'

                elif field == 'custom.qt_bore_inc_dir':
                    column = 'qt_bore_inc_dir_id_cli'

                elif field == 'custom.qt_length':
                    column = 'qt_length_id_cli'

                elif field == 'custom.qt_top_bedrock':
                    column = 'qt_top_bedrock_id_cli'

                await self.conn.execute("""
                    UPDATE public.borehole
                    SET %s = $1
                    WHERE id_bho = $2
                """ % column, value, id)

            elif field in [
                        'custom.lit_pet_top_bedrock',
                        'custom.lit_str_top_bedrock',
                        'custom.chro_str_top_bedrock'
                    ]:

                await self.conn.execute("""
                    DELETE FROM public.borehole_codelist
                    WHERE id_bho_fk = $1
                    AND code_cli = $2
                """, id, field)

                if len(value) > 0:
                    # Check if domain is extracted from the correct schema
                    check = await self.conn.fetchval("""
                        SELECT COALESCE(count(schema_cli), 0) = $1
                        FROM (
                            SELECT
                                schema_cli
                            FROM
                                codelist
                            WHERE
                                id_cli = ANY($2)
                            AND
                                schema_cli = $3
                        ) AS c
                    """, len(value), value, field)
                    if check is False:
                        raise Exception(
                            "One ore more attribute ids %s are "
                            "not part of schema %s" %
                            (
                                value, field
                            )
                        )

                    await self.conn.executemany("""
                        INSERT INTO
                            public.borehole_codelist (
                                id_bho_fk, id_cli_fk, code_cli
                            ) VALUES ($1, $2, $3)
                    """, [(id, v, field) for v in value])

            else:
                raise PatchAttributeException(field)

        except PatchAttributeException as bmsx:
            raise bmsx

        except Exception as ex:
            raise Exception("Error while updating borehole")

# -*- coding: utf-8 -*-
from bms.v1.action import Action


class CreateLayer(Action):

    async def execute(self, id, user_id):

        # Check if stratigraphy is empty
        cnt = await self.conn.fetchval("""
            SELECT
                count(id_lay)
            FROM
                bdms.layer
            WHERE
                id_sty_fk = $1
        """, id)

        depth_from = 0

        if cnt > 0:

            # Check if bedrock inserted
            bedrock = await self.conn.fetchrow("""
                SELECT
                    depth_from_lay,
                    depth_to_lay
                FROM
                    bdms.layer as l,
                    bdms.stratigraphy as s,
                    bdms.borehole as b
                WHERE
                    s.id_sty = $1
                AND
                    l.id_sty_fk = s.id_sty
                AND
                    s.id_bho_fk = b.id_bho
                AND
                    l.chronostratigraphy_id_cli = b.chronostrat_id_cli
                AND
                    l.lithology_id_cli = b.lithology_id_cli
                AND
                    l.depth_from_lay = b.top_bedrock_bho
            """, id)

            # Bedrock is not inserted
            if bedrock is None:

                print("Bedrock not inserted")

                # Just find the deepest inserted layer
                depth_from = await self.conn.fetchval("""
                    SELECT
                        depth_to_lay
                    FROM
                        bdms.layer
                    WHERE
                        id_sty_fk = $1
                    ORDER BY
                        depth_to_lay DESC NULLS LAST
                    LIMIT 1
                """, id)
            
            # Only Bedrock is inserted and start from the surface
            elif cnt == 1 and bedrock[0] == 0:

                print("Only Bedrock is inserted")

                depth_from = bedrock[1]

            # Bedrock is inserted with some other layers
            elif cnt > 1:

                print(f"Bedrock is inserted with {cnt-1} other layers")

                # Check if there is space over the bedrock
                row = await self.conn.fetchrow("""
                    SELECT
                        depth_to_lay
                    FROM
                        bdms.layer as l,
                        bdms.stratigraphy as s,
                        bdms.borehole as b
                    WHERE
                        id_sty_fk = $1
                    AND
                        l.id_sty_fk = s.id_sty
                    AND
                        s.id_bho_fk = b.id_bho
                    AND
                        depth_to_lay < top_bedrock_bho
                    ORDER BY
                        depth_to_lay DESC
                    LIMIT 1
                """, id)

                print(row, bedrock[0])

                # space found
                if row is not None and row[0] < bedrock[0]:

                    print(f"Free space found between {row[0]} and {bedrock[0]}")
                    depth_from = row[0]

                # There are some layers but not over the bedrock
                elif row is None and bedrock[0] > 0:

                    print(f"Free space found between 0 and {bedrock[0]}")
                    depth_from = 0

                # Space not present
                else:

                    # Find the last layer below the bedrock top
                    row = await self.conn.fetchrow("""
                        SELECT
                            depth_to_lay
                        FROM
                            bdms.layer as l,
                            bdms.stratigraphy as s,
                            bdms.borehole as b
                        WHERE
                            id_sty_fk = $1
                        AND
                            l.id_sty_fk = s.id_sty
                        AND
                            s.id_bho_fk = b.id_bho
                        AND
                            depth_to_lay >= top_bedrock_bho
                        ORDER BY
                            depth_to_lay DESC
                        LIMIT 1
                    """, id)

                    if row is not None:
                        depth_from = row[0]

        return {
            "id": (
                await self.conn.fetchval("""
                    INSERT INTO bdms.layer(
                        id_sty_fk, creator_lay,
                        updater_lay, depth_from_lay, depth_to_lay,
                        last_lay
                    )
                    VALUES ($1, $2, $3, $4, NULL, False) RETURNING id_lay
                """, id, user_id, user_id, depth_from)
            )
        }

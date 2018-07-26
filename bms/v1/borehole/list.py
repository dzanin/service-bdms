# -*- coding: utf-8 -*-
from bms.v1.action import Action
import math


class ListBorehole(Action):

    async def execute(self, limit=None, page=None, filter={}):

        paging = ''
        params = []
        where = []

        self.idx = 0

        def getIdx():
            self.idx += 1
            return "$%s" % self.idx

        if 'identifier' in filter.keys() and filter['identifier'] != '':
            params.append("%%%s%%" % filter['identifier'])
            where.append("""
                original_name_bho LIKE %s
            """ % getIdx())

        if 'project' in filter.keys():
            params.append(filter['project'])
            where.append("""
                project_id = %s
            """ % getIdx())

        if limit is not None and page is not None:
            paging = """
                LIMIT %s
                OFFSET %s
            """ % (getIdx(), getIdx())
            params += [
                limit, (int(limit) * (int(page) - 1))
            ]

        rowsSql = """
            SELECT
                id_bho as id,
                original_name_bho as name
            FROM
                borehole
        """

        cntSql = """
            SELECT count(*) AS cnt
            FROM borehole
        """

        if len(where) > 0:
            rowsSql += """
                WHERE %s
            """ % " AND ".join(where)
            cntSql += """
                WHERE %s
            """ % " AND ".join(where)

        sql = """
            SELECT
                array_to_json(
                    array_agg(
                        row_to_json(t)
                    )
                ),
                COALESCE((
                    %s
                ), 0)
            FROM (
                %s
            ORDER BY id_bho
                %s
            ) AS t
        """ % (cntSql, rowsSql, paging)

        rec = await self.conn.fetchrow(
            sql, *(params)
        )
        return {
            "data": self.decode(rec[0]) if rec[0] is not None else [],
            "page": page if page is not None else 1,
            "pages": math.ceil(rec[1]/limit) if limit is not None else 1,
            "rows": rec[1]
        }

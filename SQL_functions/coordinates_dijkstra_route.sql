--
--DROP FUNCTION pgr_fromAtoB(varchar, double precision, double precision, 
--                           double precision, double precision);

CREATE OR REPLACE FUNCTION pgr_fromAtoB(
                IN tbl varchar,
                IN x1 double precision,
                IN y1 double precision,
                IN x2 double precision,
                IN y2 double precision,
                OUT seq integer,
                OUT gid integer,
                OUT name text,
                OUT heading double precision,
                --OUT cost double precision,
                OUT geom geometry
        )
        RETURNS SETOF record AS
$BODY$
DECLARE
        sql     text;
        rec     record;
        source  integer;
        target  integer;
        point   integer;
        
BEGIN
        -- Find nearest node
        EXECUTE 'SELECT id::integer FROM osm_nl_2po_4pgr
                        ORDER BY geom_way <-> ST_GeometryFromText(''POINT(' 
                        || x1 || ' ' || y1 || ')'',4326) LIMIT 1' INTO rec;
        source := rec.id;
        
        EXECUTE 'SELECT id::integer FROM osm_nl_2po_4pgr 
                        ORDER BY geom_way <-> ST_GeometryFromText(''POINT(' 
                        || x2 || ' ' || y2 || ')'',4326) LIMIT 1' INTO rec;
        target := rec.id;

        -- Shortest path query (TODO: limit extent by BBOX) 
        seq := 0;
        sql := 'SELECT id, geom_way, osm_name, source, target, 
                                ST_Reverse(geom_way) AS flip_geom FROM ' ||
                        'pgr_dijkstra(''SELECT id as id, source::int, target::int, '
                                        || 'cost, reverse_cost FROM '
                                        || quote_ident(tbl) || ''', '
                                        || source || ', ' || target 
                                        || ' , false, false), '
                                || quote_ident(tbl) || ' WHERE id2 = id ORDER BY seq';

        -- Remember start point
        point := source;

        FOR rec IN EXECUTE sql
        LOOP
                -- Flip geometry (if required)
                IF ( point != rec.source ) THEN
                        rec.geom_way := rec.flip_geom;
                        point := rec.source;
                ELSE
                        point := rec.target;
                END IF;

                -- Calculate heading (simplified)
                EXECUTE 'SELECT degrees( ST_Azimuth( 
                                ST_StartPoint(''' || rec.geom_way::text || '''),
                                ST_EndPoint(''' || rec.geom_way::text || ''') ) )' 
                        INTO heading;

                -- Return record
                seq     := seq + 1;
                gid     := rec.id;
                name    := rec.osm_name;
                --cost    := rec.cost;
                geom    := rec.geom_way;
                RETURN NEXT;
        END LOOP;
        RETURN;
END;
$BODY$
LANGUAGE 'plpgsql' VOLATILE STRICT;
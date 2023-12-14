SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: create_composite_hash_range_partitions(bigint, bigint, text, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_composite_hash_range_partitions(start_timestamp bigint, time_difference bigint, partition_table text, total_partitions integer, total_sub_partitions integer) RETURNS void
    LANGUAGE plpgsql
    AS $$

   DECLARE

       start_t BIGINT;

   BEGIN

       FOR i IN 0..total_partitions-1 LOOP

           EXECUTE 'CREATE TABLE IF NOT EXISTS ' || partition_table || '_' || i || ' PARTITION OF ' || partition_table || ' FOR VALUES WITH (modulus ' || total_partitions||', remainder ' || i ||') PARTITION BY RANGE(most_recent_order)';

           start_t := start_timestamp;

           FOR j IN 0..total_sub_partitions-1 LOOP

               EXECUTE 'CREATE TABLE IF NOT EXISTS ' || partition_table || '_' || i || '_' || j || '_' || start_t || 'to' || start_t + time_difference || ' PARTITION OF ' || partition_table || '_' || i || ' FOR VALUES FROM (' || start_t || ') TO (' || start_t + time_difference || ')';

               start_t := start_t + time_difference;

           END LOOP;

       END LOOP;

   END;

$$;


--
-- Name: create_table(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_table(table_name text) RETURNS void
    LANGUAGE plpgsql
    AS $$

   BEGIN

       EXECUTE 'CREATE TABLE IF NOT EXISTS ' || table_name || '( id BIGSERIAL NOT NULL, user_id TEXT NOT NULL, sku_id TEXT NOT NULL, quantity INTEGER NOT NULL, ordered_at BIGINT[] NOT NULL, sorting_factor INTEGER NOT NULL DEFAULT 0, created_at timestamp without time zone NOT NULL, updated_at timestamp without time zone NOT NULL, most_recent_order BIGINT NOT NULL) PARTITION BY HASH (user_id)';

EXECUTE 'CREATE INDEX IF NOT EXISTS composite_user_id_sku_id_index ON ' || table_name || ' (user_id, sku_id)';

   END;

$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dummy_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dummy_users (
    id integer,
    name character varying(255),
    email character varying(255) NOT NULL
);


--
-- Name: recency_logic_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recency_logic_table (
    id bigint NOT NULL,
    lower_limit integer NOT NULL,
    value double precision NOT NULL
);


--
-- Name: recency_logic_table_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recency_logic_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recency_logic_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recency_logic_table_id_seq OWNED BY public.recency_logic_table.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: user_delivered_skus_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping (
    id bigint NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY HASH (user_id);


--
-- Name: user_delivered_skus_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_delivered_skus_mapping_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_delivered_skus_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_delivered_skus_mapping_id_seq OWNED BY public.user_delivered_skus_mapping.id;


--
-- Name: user_delivered_skus_mapping_0; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_0_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_0_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_1_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_1_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_1_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_2_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_2_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_2_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_3_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_3_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_3_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_4_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_4_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_4_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_5_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_5_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_5_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_6_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_6_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_6_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
)
PARTITION BY RANGE (most_recent_order);


--
-- Name: user_delivered_skus_mapping_7_0_1388534400to1420070400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_0_1388534400to1420070400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_1_1420070400to1451606400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_1_1420070400to1451606400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_2_1451606400to1483142400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_2_1451606400to1483142400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_3_1483142400to1514678400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_3_1483142400to1514678400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_4_1514678400to1546214400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_4_1514678400to1546214400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_5_1546214400to1577750400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_5_1546214400to1577750400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_6_1577750400to1609286400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_6_1577750400to1609286400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_7_1609286400to1640822400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_7_1609286400to1640822400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_8_1640822400to1672358400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_8_1640822400to1672358400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_7_9_1672358400to1703894400; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_delivered_skus_mapping_7_9_1672358400to1703894400 (
    id bigint DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass) NOT NULL,
    user_id text NOT NULL,
    sku_id text NOT NULL,
    quantity integer NOT NULL,
    ordered_at bigint[] NOT NULL,
    sorting_factor integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    most_recent_order bigint NOT NULL
);


--
-- Name: user_delivered_skus_mapping_0; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_0 FOR VALUES WITH (modulus 8, remainder 0);


--
-- Name: user_delivered_skus_mapping_0_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_0_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_0_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_0_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_0_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_0_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_0_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_0_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_0_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_0_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_0 ATTACH PARTITION public.user_delivered_skus_mapping_0_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_1; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_1 FOR VALUES WITH (modulus 8, remainder 1);


--
-- Name: user_delivered_skus_mapping_1_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_1_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_1_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_1_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_1_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_1_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_1_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_1_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_1_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_1_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_1 ATTACH PARTITION public.user_delivered_skus_mapping_1_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_2; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_2 FOR VALUES WITH (modulus 8, remainder 2);


--
-- Name: user_delivered_skus_mapping_2_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_2_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_2_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_2_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_2_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_2_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_2_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_2_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_2_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_2_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_2 ATTACH PARTITION public.user_delivered_skus_mapping_2_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_3; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_3 FOR VALUES WITH (modulus 8, remainder 3);


--
-- Name: user_delivered_skus_mapping_3_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_3_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_3_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_3_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_3_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_3_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_3_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_3_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_3_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_3_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_3 ATTACH PARTITION public.user_delivered_skus_mapping_3_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_4; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_4 FOR VALUES WITH (modulus 8, remainder 4);


--
-- Name: user_delivered_skus_mapping_4_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_4_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_4_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_4_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_4_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_4_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_4_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_4_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_4_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_4_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_4 ATTACH PARTITION public.user_delivered_skus_mapping_4_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_5; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_5 FOR VALUES WITH (modulus 8, remainder 5);


--
-- Name: user_delivered_skus_mapping_5_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_5_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_5_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_5_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_5_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_5_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_5_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_5_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_5_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_5_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_5 ATTACH PARTITION public.user_delivered_skus_mapping_5_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_6; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_6 FOR VALUES WITH (modulus 8, remainder 6);


--
-- Name: user_delivered_skus_mapping_6_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_6_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_6_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_6_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_6_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_6_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_6_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_6_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_6_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_6_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_6 ATTACH PARTITION public.user_delivered_skus_mapping_6_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: user_delivered_skus_mapping_7; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ATTACH PARTITION public.user_delivered_skus_mapping_7 FOR VALUES WITH (modulus 8, remainder 7);


--
-- Name: user_delivered_skus_mapping_7_0_1388534400to1420070400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_0_1388534400to1420070400 FOR VALUES FROM ('1388534400') TO ('1420070400');


--
-- Name: user_delivered_skus_mapping_7_1_1420070400to1451606400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_1_1420070400to1451606400 FOR VALUES FROM ('1420070400') TO ('1451606400');


--
-- Name: user_delivered_skus_mapping_7_2_1451606400to1483142400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_2_1451606400to1483142400 FOR VALUES FROM ('1451606400') TO ('1483142400');


--
-- Name: user_delivered_skus_mapping_7_3_1483142400to1514678400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_3_1483142400to1514678400 FOR VALUES FROM ('1483142400') TO ('1514678400');


--
-- Name: user_delivered_skus_mapping_7_4_1514678400to1546214400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_4_1514678400to1546214400 FOR VALUES FROM ('1514678400') TO ('1546214400');


--
-- Name: user_delivered_skus_mapping_7_5_1546214400to1577750400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_5_1546214400to1577750400 FOR VALUES FROM ('1546214400') TO ('1577750400');


--
-- Name: user_delivered_skus_mapping_7_6_1577750400to1609286400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_6_1577750400to1609286400 FOR VALUES FROM ('1577750400') TO ('1609286400');


--
-- Name: user_delivered_skus_mapping_7_7_1609286400to1640822400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_7_1609286400to1640822400 FOR VALUES FROM ('1609286400') TO ('1640822400');


--
-- Name: user_delivered_skus_mapping_7_8_1640822400to1672358400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_8_1640822400to1672358400 FOR VALUES FROM ('1640822400') TO ('1672358400');


--
-- Name: user_delivered_skus_mapping_7_9_1672358400to1703894400; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping_7 ATTACH PARTITION public.user_delivered_skus_mapping_7_9_1672358400to1703894400 FOR VALUES FROM ('1672358400') TO ('1703894400');


--
-- Name: recency_logic_table id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recency_logic_table ALTER COLUMN id SET DEFAULT nextval('public.recency_logic_table_id_seq'::regclass);


--
-- Name: user_delivered_skus_mapping id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_delivered_skus_mapping ALTER COLUMN id SET DEFAULT nextval('public.user_delivered_skus_mapping_id_seq'::regclass);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: composite_user_id_sku_id_index; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX composite_user_id_sku_id_index ON ONLY public.user_delivered_skus_mapping USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_0 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_0_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_0_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_1 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_1_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_1_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_1_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_2 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_2_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_2_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_2_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_3 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_3_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_3_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_3_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_4 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_4_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_4_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_4_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_5 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_5_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_5_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_5_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_6 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_6_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_6_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_6_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_user_id_sku_id_idx ON ONLY public.user_delivered_skus_mapping_7 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_0_1388534400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_0_1388534400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_0_1388534400to1420070400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_1_1420070400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_1_1420070400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_1_1420070400to1451606400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_2_1451606400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_2_1451606400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_2_1451606400to1483142400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_3_1483142400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_3_1483142400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_3_1483142400to1514678400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_4_1514678400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_4_1514678400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_4_1514678400to1546214400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_5_1546214400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_5_1546214400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_5_1546214400to1577750400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_6_1577750400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_6_1577750400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_6_1577750400to1609286400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_7_1609286400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_7_1609286400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_7_1609286400to1640822400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_8_1640822400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_8_1640822400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_8_1640822400to1672358400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_7_9_1672358400to_user_id_sku_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_delivered_skus_mapping_7_9_1672358400to_user_id_sku_id_idx ON public.user_delivered_skus_mapping_7_9_1672358400to1703894400 USING btree (user_id, sku_id);


--
-- Name: user_delivered_skus_mapping_0_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_0_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_0_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_0_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_0_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_1_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_1_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_1_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_1_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_2_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_2_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_2_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_2_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_3_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_3_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_3_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_3_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_4_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_4_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_4_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_4_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_5_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_5_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_5_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_5_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_6_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_6_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_6_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_6_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_0_1388534400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_0_1388534400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_1_1420070400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_1_1420070400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_2_1451606400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_2_1451606400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_3_1483142400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_3_1483142400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_4_1514678400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_4_1514678400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_5_1546214400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_5_1546214400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_6_1577750400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_6_1577750400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_7_1609286400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_7_1609286400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_8_1640822400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_8_1640822400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_9_1672358400to_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.user_delivered_skus_mapping_7_user_id_sku_id_idx ATTACH PARTITION public.user_delivered_skus_mapping_7_9_1672358400to_user_id_sku_id_idx;


--
-- Name: user_delivered_skus_mapping_7_user_id_sku_id_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.composite_user_id_sku_id_index ATTACH PARTITION public.user_delivered_skus_mapping_7_user_id_sku_id_idx;


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20220617090653');

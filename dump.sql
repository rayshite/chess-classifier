--
-- PostgreSQL database dump
--

\restrict iyTkQzidD1tAj1kBex6fvfjjbOagYQGSQDdiV5SeXTX7pMTYwJW9GFVyYE7qa46

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

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
-- Name: game_status; Type: TYPE; Schema: public; Owner: app_user
--

CREATE TYPE public.game_status AS ENUM (
    'in_progress',
    'finished'
);


ALTER TYPE public.game_status OWNER TO app_user;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: app_user
--

CREATE TYPE public.user_role AS ENUM (
    'student',
    'teacher',
    'admin'
);


ALTER TYPE public.user_role OWNER TO app_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO app_user;

--
-- Name: games; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.games (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    status public.game_status DEFAULT 'in_progress'::public.game_status NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    player1_id integer NOT NULL,
    player2_id integer NOT NULL
);


ALTER TABLE public.games OWNER TO app_user;

--
-- Name: games_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.games_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.games_id_seq OWNER TO app_user;

--
-- Name: games_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.games_id_seq OWNED BY public.games.id;


--
-- Name: snapshots; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.snapshots (
    id integer NOT NULL,
    game_id integer NOT NULL,
    "position" text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.snapshots OWNER TO app_user;

--
-- Name: snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.snapshots_id_seq OWNER TO app_user;

--
-- Name: snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.snapshots_id_seq OWNED BY public.snapshots.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    name character varying(100) NOT NULL,
    role public.user_role DEFAULT 'student'::public.user_role NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    is_superuser boolean DEFAULT false NOT NULL,
    is_verified boolean DEFAULT false NOT NULL
);


ALTER TABLE public.users OWNER TO app_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO app_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: games id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.games ALTER COLUMN id SET DEFAULT nextval('public.games_id_seq'::regclass);


--
-- Name: snapshots id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.snapshots ALTER COLUMN id SET DEFAULT nextval('public.snapshots_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: app_user
--

INSERT INTO public.alembic_version (version_num) VALUES ('003');


--
-- Data for Name: games; Type: TABLE DATA; Schema: public; Owner: app_user
--



--
-- Data for Name: snapshots; Type: TABLE DATA; Schema: public; Owner: app_user
--



--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: app_user
--

INSERT INTO public.users (id, email, hashed_password, name, role, is_active, created_at, is_superuser, is_verified) VALUES (1, 'admin@example.com', '$argon2id$v=19$m=65536,t=3,p=4$t+swrG6tKCnNCDLJkDWmSw$2BJ6tBr1nD3MtdyVH/7X8aZwEXOhMAy88b74KxVYndE', 'Администратор', 'admin', true, '2026-02-04 14:02:16.631452+00', true, true);


--
-- Name: games_id_seq; Type: SEQUENCE SET; Schema: public; Owner: app_user
--

SELECT pg_catalog.setval('public.games_id_seq', 1, false);


--
-- Name: snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: app_user
--

SELECT pg_catalog.setval('public.snapshots_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: app_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: games games_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_pkey PRIMARY KEY (id);


--
-- Name: snapshots snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.snapshots
    ADD CONSTRAINT snapshots_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_games_player1_id; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX ix_games_player1_id ON public.games USING btree (player1_id);


--
-- Name: ix_games_player2_id; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX ix_games_player2_id ON public.games USING btree (player2_id);


--
-- Name: ix_games_status; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX ix_games_status ON public.games USING btree (status);


--
-- Name: ix_snapshots_game_id; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX ix_snapshots_game_id ON public.snapshots USING btree (game_id);


--
-- Name: games games_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: games games_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: snapshots snapshots_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.snapshots
    ADD CONSTRAINT snapshots_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.games(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict iyTkQzidD1tAj1kBex6fvfjjbOagYQGSQDdiV5SeXTX7pMTYwJW9GFVyYE7qa46


-- schema.sql · Le tabelle del database.
-- La fonte vera: se c'è un dubbio, comanda lui.
--
-- Cinque tabelle:
--   utente          chi usa l'app
--   bug             la scheda di un errore: cosa è successo, perché, come si risolve
--   tecnologia      git, python, java...: condivise tra tutti gli utenti
--   bug_tecnologia  quali tecnologie ha ogni bug (molti a molti)
--   ripetizione     ogni volta che un bug capita (la prima volta e ogni "Mi è ricapitato")
--
-- Regole che il database NON può controllare da solo, e che controlla l'API:
--   - un bug deve avere almeno una tecnologia
--   - titolo (se vuoto) ed errore_normalizzato si calcolano in Python dall'errore
--   - quando si crea un bug, si crea anche la sua prima ripetizione
--
-- Si esegue su un database vuoto: crea tutto da zero.

-- Estensione per la ricerca per somiglianza (funzione similarity, operatore %).
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- ─────────────────────────────────────────────────────────────
-- UTENTE · chi usa l'app
-- ─────────────────────────────────────────────────────────────
CREATE TABLE utente (
    id             SERIAL       PRIMARY KEY,
    email          TEXT         NOT NULL UNIQUE,
    nome           TEXT         NOT NULL,
    password_hash  TEXT         NOT NULL,              -- mai la password in chiaro (argon2)
    creato_il      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT email_minuscola CHECK (email = lower(email))
);


-- ─────────────────────────────────────────────────────────────
-- BUG · la scheda di un errore
-- ─────────────────────────────────────────────────────────────
CREATE TABLE bug (
    id                   SERIAL       PRIMARY KEY,
    utente_id            INT          NOT NULL REFERENCES utente(id) ON DELETE CASCADE,

    -- scritti dall'utente
    titolo               TEXT         NOT NULL,         -- se vuoto, l'API usa l'ultima riga dell'errore
    errore               TEXT         NOT NULL,         -- il messaggio incollato, così com'è
    causa                TEXT         NOT NULL,         -- perché è successo
    soluzione            TEXT         NOT NULL,         -- come l'ho risolto

    -- calcolato dall'API al salvataggio: serve alla ricerca.
    -- È l'ultima riga dell'errore, in minuscolo, senza percorsi e numeri di riga,
    -- così lo stesso errore si ritrova anche se nasce in un altro progetto.
    errore_normalizzato  TEXT         NOT NULL,

    creato_il            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    modificato_il        TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- "obbligatorio" vuol dire anche "non fatto solo di spazi"
    CONSTRAINT titolo_non_vuoto    CHECK (btrim(titolo)    <> ''),
    CONSTRAINT errore_non_vuoto    CHECK (btrim(errore)    <> ''),
    CONSTRAINT causa_non_vuota     CHECK (btrim(causa)     <> ''),
    CONSTRAINT soluzione_non_vuota CHECK (btrim(soluzione) <> ''),
    CONSTRAINT titolo_breve        CHECK (length(titolo) <= 80)
);

-- l'elenco "i miei bug" filtra sempre per utente
CREATE INDEX bug_utente_idx ON bug (utente_id);

-- ricerca per somiglianza sull'errore incollato
CREATE INDEX bug_errore_trgm_idx ON bug USING gin (errore_normalizzato gin_trgm_ops);


-- ─────────────────────────────────────────────────────────────
-- TECNOLOGIA · git, python, java...: condivise tra tutti gli utenti
-- ─────────────────────────────────────────────────────────────
CREATE TABLE tecnologia (
    id    SERIAL  PRIMARY KEY,
    nome  TEXT    NOT NULL UNIQUE,                     -- Git, git e GIT diventano una sola

    CONSTRAINT tecnologia_minuscola CHECK (nome = lower(nome)),
    CONSTRAINT tecnologia_non_vuota CHECK (btrim(nome) <> '')
);


-- ─────────────────────────────────────────────────────────────
-- BUG_TECNOLOGIA · quali tecnologie ha ogni bug
-- (un bug ha più tecnologie, una tecnologia sta su più bug)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE bug_tecnologia (
    bug_id         INT  NOT NULL REFERENCES bug(id)        ON DELETE CASCADE,
    tecnologia_id  INT  NOT NULL REFERENCES tecnologia(id) ON DELETE CASCADE,

    PRIMARY KEY (bug_id, tecnologia_id)                -- la stessa tecnologia una volta sola per bug
);

-- l'autocompletamento parte dalla tecnologia per trovare i bug dell'utente
CREATE INDEX bug_tecnologia_tecnologia_idx ON bug_tecnologia (tecnologia_id);


-- ─────────────────────────────────────────────────────────────
-- RIPETIZIONE · ogni volta che un bug capita
-- ─────────────────────────────────────────────────────────────
CREATE TABLE ripetizione (
    id            SERIAL       PRIMARY KEY,
    bug_id        INT          NOT NULL REFERENCES bug(id) ON DELETE CASCADE,
    data          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    minuti_persi  INT,                                  -- facoltativo; 120 vuol dire "120 o più"
    commento      TEXT,                                 -- facoltativo

    CONSTRAINT minuti_fissi CHECK (minuti_persi IN (5, 15, 30, 60, 120))
);

-- contare le ripetizioni di un bug
CREATE INDEX ripetizione_bug_idx ON ripetizione (bug_id);

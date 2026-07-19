-- =====================================================================
-- 🕌 ARCHITECTURE DE LA BASE DE DONNÉES CLOUD HAYAATI (POSTGRESQL)
-- Version 5.5 - Intégration complète du volet avicole (Volailles).
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS arbre_genealogique CASCADE;
DROP TABLE IF EXISTS mouhasabah_journaliere CASCADE;
DROP TABLE IF EXISTS dettes CASCADE;
DROP TABLE IF EXISTS profils_sharia CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 🔹 TABLE 1 : USERS (Profil civil)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prenom VARCHAR(60) NOT NULL, nom VARCHAR(60) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    pays VARCHAR(100) NOT NULL, ville VARCHAR(100) NOT NULL,
    telephone VARCHAR(30) NOT NULL, date_naissance_gregorienne DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 TABLE 2 : PROFILS_SHARIA (Variables de Fiqh & Inventaire Patrimonial Global)
CREATE TABLE profils_sharia (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    madhhab_actif VARCHAR(15) NOT NULL DEFAULT 'Maliki',
    devise_active VARCHAR(10) NOT NULL DEFAULT 'CFA',
    ajustement_hegiri_jours INT NOT NULL DEFAULT 0,
    capital_brut_declaré NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    valeur_bijoux_or NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    valeur_stock_marchand NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    liquidites_entreprise NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    valeur_immeubles NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    valeur_logistique NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    poids_recolte_kg NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    valeur_recolte_stockee NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    nombre_ovins INT NOT NULL DEFAULT 0,
    valeur_troupeau_ovins NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    nombre_bovins INT NOT NULL DEFAULT 0,
    valeur_troupeau_bovins NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    -- 🚨 MISE À JOUR : Colonnes réelles pour stocker l'inventaire avicole (Volailles)
    nombre_volailles INT NOT NULL DEFAULT 0,
    valeur_volailles NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    wasiyya_testament_textuel TEXT,
    montant_legs_volontaire NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    date_ouverture_nissab_gregorienne DATE
);

-- 🔹 TABLE 3 : DETTES (Matrice comptable)
CREATE TABLE dettes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type_dette VARCHAR(10) NOT NULL,
    statut_recouvrement VARCHAR(15) NOT NULL,
    montant NUMERIC(15, 2) NOT NULL,
    description TEXT NOT NULL,
    date_declaration DATE NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT chk_type_dette CHECK (type_dette IN ('PASSIVE', 'ACTIVE')),
    CONSTRAINT chk_statut_recouvrement CHECK (statut_recouvrement IN ('SOLVABLE', 'INCERTAIN'))
);

-- 🔹 TABLE 4 : MOUHASABAH_JOURNALIERE (Livre spirituel)
CREATE TABLE mouhasabah_journaliere (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_gregorienne DATE NOT NULL DEFAULT CURRENT_DATE,
    date_hegirienne_calculee VARCHAR(30) NOT NULL,
    prieres_obligatoires_validees INT NOT NULL DEFAULT 0,
    rakahs_nawafil INT NOT NULL DEFAULT 0,
    jeune_jour_valide BOOLEAN NOT NULL DEFAULT FALSE,
    type_jeune VARCHAR(15) DEFAULT 'AUCUN',
    sadaqah_versee NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    lecture_coran_pages INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_prieres CHECK (prieres_obligatoires_validees BETWEEN 0 AND 5),
    CONSTRAINT chk_type_jeune CHECK (type_jeune IN ('AUCUN', 'RAMADAN', 'JOUR_BLANC', 'ARAFA', 'ACHOURA', 'SUREROGATOIRE')),
    UNIQUE (user_id, date_gregorienne)
);

-- 🔹 TABLE 5 : ARBRE_GENEALOGIQUE (Héritage)
CREATE TABLE arbre_genealogique (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lien_parente VARCHAR(20) NOT NULL,
    nombre INT NOT NULL DEFAULT 1,
    est_exclu_indignite BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_parente CHECK (lien_parente IN ('epouse', 'epoux', 'fils', 'fille', 'pere', 'mere', 'grand_pere', 'frere_germain', 'frere_uterin', 'oncle')),
    UNIQUE (user_id, lien_parente)
);

CREATE INDEX idx_dettes_user ON dettes(user_id, type_dette);
CREATE INDEX idx_mouhasabah_date ON mouhasabah_journaliere(user_id, date_gregorienne);
CREATE INDEX idx_arbre_user ON arbre_genealogique(user_id);

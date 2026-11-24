import json

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Sentence


def _tok(
    target: str,
    stem: str,
    inflection: str,
    stem_distractors: list[str],
    inflection_distractors: list[str],
    gradation: str | None = None,
) -> dict:
    return {
        "target": target,
        "stem": stem,
        "inflection": inflection,
        "gradation": gradation,
        "stem_distractors": stem_distractors,
        "inflection_distractors": inflection_distractors,
    }


SEED_SENTENCES = [
    (
        "I drink coffee every morning.",
        "easy",
        [
            _tok("Minä", "minä", "nominative (base)", ["sinä", "hän", "me"], ["minua", "minun", "minulla"]),
            _tok("juon", "juoda", "1st sg present (-n)", ["syödä", "ostaa", "tehdä"], ["juo", "juot", "juomme"]),
            _tok("kahvia", "kahvi", "partitive (-a)", ["tee", "vesi", "maito"], ["kahvi", "kahvin", "kahvissa"]),
            _tok("joka", "joka", "indeclinable", ["kaikki", "tämä", "mikä"], ["jota", "jonka", "jossa"]),
            _tok("aamu", "aamu", "nominative (with joka)", ["ilta", "päivä", "yö"], ["aamua", "aamun", "aamulla"]),
        ],
    ),
    (
        "The dog is sleeping under the table.",
        "easy",
        [
            _tok("Koira", "koira", "nominative (base)", ["kissa", "lintu", "karhu"], ["koiraa", "koiran", "koiralla"]),
            _tok("nukkuu", "nukkua", "3rd sg present (kk -> k)", ["herätä", "juosta", "istua"], ["nukun", "nukut", "nukkuvat"], "kk -> k (strong in 3rd sg)"),
            _tok("pöydän", "pöytä", "genitive (-n, t -> d)", ["tuoli", "sohva", "sänky"], ["pöytä", "pöytää", "pöydällä"], "t -> d"),
            _tok("alla", "alla", "postposition", ["päällä", "vieressä", "takana"], ["alle", "alta", "alapuolella"]),
        ],
    ),
    (
        "I read a book at home.",
        "easy",
        [
            _tok("Minä", "minä", "nominative (base)", ["sinä", "hän", "te"], ["minun", "minua", "minulle"]),
            _tok("luen", "lukea", "1st sg present (k -> Ø)", ["kirjoittaa", "katsoa", "ostaa"], ["lukee", "luet", "lukevat"], "k -> Ø"),
            _tok("kirjaa", "kirja", "partitive (-a)", ["lehti", "sana", "kynä"], ["kirja", "kirjan", "kirjassa"]),
            _tok("kotona", "koti", "essive-like locative", ["koulu", "kauppa", "työ"], ["koti", "kodin", "kodissa"], "t -> d in koti stem"),
        ],
    ),
    (
        "We are going to the lake tomorrow.",
        "medium",
        [
            _tok("Me", "me", "nominative plural", ["te", "he", "minä"], ["meitä", "meidän", "meillä"]),
            _tok("menemme", "mennä", "1st pl present (-mme)", ["tulla", "lähteä", "ajaa"], ["menee", "menen", "menevät"]),
            _tok("järvelle", "järvi", "allative (-lle)", ["meri", "joki", "metsä"], ["järvi", "järvessä", "järven"]),
            _tok("huomenna", "huomenna", "adverb", ["eilen", "tänään", "nyt"], ["huomen", "huomiseen", "huomisen"]),
        ],
    ),
    (
        "My friend lives in a big house.",
        "medium",
        [
            _tok("Ystäväni", "ystävä", "nominative + 1st sg possessive (-ni)", ["naapuri", "veli", "opettaja"], ["ystävä", "ystäväsi", "ystävän"]),
            _tok("asuu", "asua", "3rd sg present", ["työskennellä", "kävellä", "nukkua"], ["asun", "asut", "asuvat"]),
            _tok("isossa", "iso", "inessive (-ssa)", ["pieni", "vanha", "uusi"], ["iso", "ison", "isoon"]),
            _tok("talossa", "talo", "inessive (-ssa)", ["huone", "kaupunki", "kylä"], ["talo", "talon", "taloon"]),
        ],
    ),
    (
        "They buy fresh bread from the shop.",
        "medium",
        [
            _tok("He", "he", "nominative plural", ["me", "te", "ne"], ["heitä", "heidän", "heillä"]),
            _tok("ostavat", "ostaa", "3rd pl present (-vat)", ["myydä", "tehdä", "tuoda"], ["ostaa", "ostan", "ostamme"]),
            _tok("tuoretta", "tuore", "partitive (-tta)", ["vanha", "lämmin", "hyvä"], ["tuore", "tuoreen", "tuoreessa"]),
            _tok("leipää", "leipä", "partitive (-ä)", ["juusto", "kakku", "maito"], ["leipä", "leivän", "leivässä"], "p -> v in weak grade"),
            _tok("kaupasta", "kauppa", "elative (-sta, pp -> p)", ["tori", "koti", "keittiö"], ["kauppa", "kaupassa", "kauppaan"], "pp -> p"),
        ],
    ),
    (
        "She has never visited the northern part of the country.",
        "hard",
        [
            _tok("Hän", "hän", "nominative (base)", ["minä", "sinä", "he"], ["häntä", "hänen", "hänellä"]),
            _tok("ei", "ei", "negative verb (3rd sg)", ["en", "et", "eivät"], ["olla", "ole", "ollut"]),
            _tok("ole", "olla", "connegative present", ["käydä", "tulla", "mennä"], ["on", "oli", "ollut"]),
            _tok("koskaan", "koskaan", "adverb (with negation)", ["aina", "joskus", "usein"], ["kerran", "vielä", "nyt"]),
            _tok("käynyt", "käydä", "past participle (-nyt)", ["asunut", "matkustanut", "nähnyt"], ["käy", "kävi", "käyvät"]),
            _tok("maan", "maa", "genitive (-n)", ["kaupunki", "alue", "saari"], ["maa", "maata", "maassa"]),
            _tok("pohjoisosassa", "pohjoisosa", "compound + inessive (-ssa)", ["eteläosa", "keskusta", "länsiranta"], ["pohjoisosa", "pohjoisosan", "pohjoisosaan"]),
        ],
    ),
    (
        "The children are playing with their dog in the garden.",
        "hard",
        [
            _tok("Lapset", "lapsi", "nominative plural (-t)", ["aikuiset", "nuoret", "tytöt"], ["lapsi", "lapsia", "lasten"]),
            _tok("leikkivät", "leikkiä", "3rd pl present (-vät)", ["juosta", "laulaa", "lukea"], ["leikkii", "leikin", "leikimme"], "kk -> k in weak grade"),
            _tok("koiransa", "koira", "genitive + 3rd possessive (-nsa)", ["kissa", "pallo", "ystävä"], ["koira", "koiran", "koiraa"]),
            _tok("kanssa", "kanssa", "postposition", ["luona", "takana", "edessä"], ["mukana", "ilman", "kohti"]),
            _tok("puutarhassa", "puutarha", "inessive (-ssa)", ["metsä", "puisto", "piha"], ["puutarha", "puutarhan", "puutarhaan"]),
        ],
    ),
    (
        "We must leave early because the train leaves soon.",
        "hard",
        [
            _tok("Meidän", "me", "genitive (necessive subject)", ["teidän", "heidän", "minun"], ["me", "meitä", "meillä"]),
            _tok("täytyy", "täytyä", "3rd sg necessive verb", ["pitää", "haluta", "voida"], ["täydyn", "täytyvät", "täytyi"]),
            _tok("lähteä", "lähteä", "1st infinitive", ["mennä", "tulla", "jäädä"], ["lähden", "lähtee", "lähtevät"], "t -> d in inflected forms"),
            _tok("aikaisin", "aikaisin", "adverb", ["myöhään", "nopeasti", "hitaasti"], ["aikainen", "aika", "ajoissa"]),
            _tok("koska", "koska", "conjunction", ["kun", "että", "mutta"], ["vaikka", "joten", "sillä"]),
            _tok("juna", "juna", "nominative", ["bussi", "auto", "laiva"], ["junan", "junaa", "junassa"]),
            _tok("lähtee", "lähteä", "3rd sg present", ["saapua", "pysähtyä", "ajaa"], ["lähden", "lähtevät", "lähti"]),
            _tok("pian", "pian", "adverb", ["myöhemmin", "eilen", "harvoin"], ["nopea", "heti", "kohta"]),
        ],
    ),
]


def seed_sentences() -> None:
    with SessionLocal() as db:
        existing_count = db.scalar(select(func.count(Sentence.id))) or 0
        if existing_count == 0:
            db.add_all(
                Sentence(
                    text=text,
                    difficulty=difficulty,
                    target_tokens_json=json.dumps(tokens, ensure_ascii=False),
                )
                for text, difficulty, tokens in SEED_SENTENCES
            )
            db.commit()

import json
import logging
import sys

from hellofedge.logs import JsonFormatter, setup_logging


def make_record(msg="bonjour %s", args=("Cotonou",), exc_info=None, **extra):
    record = logging.LogRecord(
        "hellofedge.test", logging.WARNING, __file__, 1, msg, args, exc_info
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formats_a_record_as_one_json_line():
    line = JsonFormatter().format(make_record())

    entry = json.loads(line)
    assert "\n" not in line
    assert entry["level"] == "WARNING"
    assert entry["logger"] == "hellofedge.test"
    assert entry["msg"] == "bonjour Cotonou"


def test_timestamps_are_in_utc():
    record = make_record()
    record.created = 0.0

    entry = json.loads(JsonFormatter().format(record))

    assert entry["ts"] == "1970-01-01T00:00:00+00:00"


def test_keeps_accented_characters_readable():
    line = JsonFormatter().format(make_record(msg="worker arrêté", args=()))

    assert "arrêté" in line


def test_merges_the_data_dictionary_into_the_entry():
    entry = json.loads(
        JsonFormatter().format(make_record(data={"pair": "USD/JPY", "tf": "M1"}))
    )

    assert entry["pair"] == "USD/JPY"
    assert entry["tf"] == "M1"


def test_ignores_a_data_attribute_that_is_not_a_dictionary():
    entry = json.loads(JsonFormatter().format(make_record(data="pas un dict")))

    assert "data" not in entry
    assert entry["msg"] == "bonjour Cotonou"


def test_serialises_values_json_does_not_know_as_text():
    entry = json.loads(JsonFormatter().format(make_record(data={"when": object()})))

    assert isinstance(entry["when"], str)


def test_includes_the_traceback_when_an_exception_is_logged():
    try:
        raise ValueError("boum")
    except ValueError:
        record = make_record(exc_info=sys.exc_info())

    entry = json.loads(JsonFormatter().format(record))

    assert "ValueError: boum" in entry["exc"]


def test_setup_logging_writes_json_to_standard_output(capsys):
    setup_logging("INFO")

    logging.getLogger("hellofedge.test").info("prêt")

    entry = json.loads(capsys.readouterr().out.strip())
    assert entry["msg"] == "prêt"


def test_setup_logging_applies_the_requested_level(capsys):
    setup_logging("WARNING")

    logging.getLogger("hellofedge.test").info("trop bavard")

    assert capsys.readouterr().out == ""


def test_setup_logging_routes_uvicorn_logs_through_the_json_format(capsys):
    logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler(sys.stdout))

    setup_logging("INFO")
    logging.getLogger("uvicorn.access").info("GET /api/health 200")

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["logger"] == "uvicorn.access"

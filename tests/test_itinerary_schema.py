from app.schemas.itinerary import Itinerary

def test_schema_builds():
    # Ensures the schema can be created without url format="uri"
    schema = Itinerary.model_json_schema()
    schema_str = str(schema).lower()
    assert '"format': 'uri'' not in schema_str
    assert '"format": "uri"' not in schema_str

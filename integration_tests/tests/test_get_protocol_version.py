from integration_tests.helpers.message_loader import load_message


def test_get_protocol_version(grpc_client):
    message = load_message("GetProtocolVersion")
    response = grpc_client.get_protocol_version(message)
    assert response is not None
    assert response.protocol_version != ""
    print(f"Protocol version: {response.protocol_version}")

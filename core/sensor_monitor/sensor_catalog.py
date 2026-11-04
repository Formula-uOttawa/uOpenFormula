"""The first eight sensor types: brake pressure has two separate channels.

These names describe the currently supported CSV export. Adding aliases later
must be explicit so an unrelated channel never silently supplies a sensor.
"""

SENSORS = (
    {"id": "gear", "name": "Gear position", "channel": "Gear Position", "group": "Drivetrain", "plot": "step"},
    {"id": "brake_front", "name": "Front brake pressure", "channel": "Front Brake Pres", "aliases": ["BRK PRESS F"], "group": "Braking", "plot": "line"},
    {"id": "brake_rear", "name": "Rear brake pressure", "channel": "Rear Brake Pres", "aliases": ["BRK PRESS R"], "group": "Braking", "plot": "line"},
    {"id": "throttle", "name": "Throttle position", "channel": "ECU THROTTLE", "group": "Engine", "plot": "line"},
    {"id": "iat", "name": "Intake air temperature", "channel": "ECU IAT", "group": "Engine", "plot": "line"},
    {"id": "map", "name": "Manifold air pressure", "channel": "ECU MAP", "group": "Engine", "plot": "line"},
    {"id": "fuel", "name": "Fuel pressure", "channel": "ECU FUEL P", "group": "Engine", "plot": "line"},
    {"id": "coolant", "name": "Coolant temperature", "channel": "ECU ECT", "group": "Cooling", "plot": "line"},
    {"id": "lambda", "name": "Lambda", "channel": "EXHAUST LAMBDA", "group": "Combustion", "plot": "line"},
)

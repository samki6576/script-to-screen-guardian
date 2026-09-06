USE production_db;

INSERT INTO equipment_inventory (equipment_name, category, status, location) VALUES
    ('ARRI_Alexa', 'camera', 'available', 'Main Warehouse'),
    ('lighting_kit', 'lighting', 'booked_until_2026-09-14', 'Studio B'),
    ('rain_machine', 'fx', 'maintenance_scheduled', 'FX Storage'),
    ('foley_kit', 'sound', 'available', 'Sound Stage 2'),
    ('stunt_rigging', 'safety', 'available', 'Main Warehouse'),
    ('generator_lighting', 'lighting', 'available', 'Studio B');

INSERT INTO crew_schedules (crew_member, role, shoot_date, is_available, conflict_reason) VALUES
    ('Alex Rivera', 'Gaffer', '2026-09-10', 0, 'Booked on another production'),
    ('Jordan Lee', 'Sound Mixer', '2026-09-10', 1, ''),
    ('Priya Nair', 'Stunt Coordinator', '2026-09-15', 1, '');

INSERT INTO maintenance_logs (equipment_name, maintenance_date, notes) VALUES
    ('rain_machine', '2026-09-13', 'Scheduled pump seal replacement');

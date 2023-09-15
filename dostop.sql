GRANT CONNECT ON DATABASE sem2023_matean TO javnost;
GRANT USAGE ON SCHEMA public TO javnost;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO javnost;

GRANT INSERT ON osebe TO javnost;
GRANT INSERT ON drzava TO javnost;
GRANT INSERT ON mesto TO javnost;
GRANT INSERT ON skupine TO javnost;
GRANT UPDATE ON vlak TO javnost;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO javnost;
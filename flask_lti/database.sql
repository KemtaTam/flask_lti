CREATE TABLE IF NOT EXISTS keysecret (
	key text NOT NULL,
	secret text NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
	id integer PRIMARY KEY AUTOINCREMENT,
	user_id text NOT NULL,
	name text NOT NULL,
	email text NOT NULL,
	attempts integer NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
	id integer PRIMARY KEY AUTOINCREMENT,
	session_id text,
	task text,
	lis_outcome_service_url text,
	lis_result_sourcedid text,
	oauth_consumer_key,
	admin integer
);

CREATE TABLE IF NOT EXISTS solutions (
	id integer PRIMARY KEY AUTOINCREMENT,
	solution_id text,
	userid text,
	task text,
	score text,
	lis_outcome_service_url text,
	lis_result_sourcedid text,
	oauth_consumer_key,
	is_passbacked integer
);

CREATE TABLE IF NOT EXISTS params (
	id integer PRIMARY KEY AUTOINCREMENT,
	passback_params text
);


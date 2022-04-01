pragma foreign_keys = on;
pragma journal_mode = off;
pragma synchronous = off;

create table if not exists chatter (
    id integer primary key
    , name text unique not null
    , display_name text unique not null
    , history text
);

create table if not exists channel (
    id integer primary key
    -- id text primary key
    , name text unique not null
    , display_name text unique not null
    -- , history text
);

create table if not exists user_presence (
    id integer unique not null
    , user_id integer not null
    , channel_id integer not null
    , primary key(user_id, channel_id)
    , foreign key(user_id) references chatter(id)
    , foreign key(channel_id) references channel(id)
);

create table if not exists user_chan_data (
    presence_id integer primary key
    , rank text
    , msgs_sent integer
    , watched_since text
    , history text
    , foreign key(presence_id) references user_presence(id)
);

create table if not exists variable (
    id integer primary key
    , var_name text unique not null
);

create table if not exists chan_var (
    id integer primary key
    , channel_id integer not null
    , var_id integer not null
    , value text
    , foreign key(channel_id) references channel(id)
    , foreign key(var_id) references variable(id)
);

create table if not exists user_var (
    id integer primary key
    , user_id integer not null
    , var_id integer not null
    , value text
    , foreign key(user_id) references chatter(id)
    , foreign key(var_id) references variable(id)
);

create table if not exists command (
    id integer primary key
    , channel_id integer not null
    , name text unique not null
    , message text
    , aliases text
    , perms text not null
    , count integer
    , is_hidden integer not null
    , override_builtin integer -- not null
    , is_enabled integer not null
    , author_id integer not null
    , modified_by integer
    , modified_on text
    , ctime text -- not null
    , mtime text -- not null
    , foreign key(channel_id) references channel(id)
);

create table if not exists user_cmd_data (
    user_id integer not null
    , cmd_id integer not null
    , user_cmd_count integer
    , foreign key(user_id) references chatter(id)
    , foreign key(cmd_id) references command(id)
    , primary key(user_id, cmd_id)
);

pragma foreign_keys = on;
pragma journal_mode = off;
pragma synchronous = off;

create table if not exists chatter (
    id integer primary key
    , name text unique not null
    -- , display_name text unique not null
);

create table if not exists channel (
    id integer primary key
    , name text unique not null
    , join_date int not null
    -- , command_prefix text
    , min_perms text
);

create table if not exists user_presence (
    id integer unique not null
    , user_id integer not null
    , channel_id integer not null
    , user_rank text
    , messages_sent integer not null
    , active_since integer not null
    , primary key (user_id, channel_id)
    , foreign key (user_id) references chatter(id)
    , foreign key (channel_id) references channel(id)
);

create table if not exists custom_variable (
    id integer primary key
    , channel_id integer not null
    , name text
    , value text
    , foreign key (channel_id) references channel(id)
);

create table if not exists built_in_command (
    id integer primary key
    , name text unique not null
    , global_aliases text
);

create table if not exists channel_built_in_data (
    command_id integer not null
    , channel_id integer not null
    , aliases text
    , perms text not null
    , count integer
    , cooldowns json -- e.g.: "10,5,0,'Weebs':30" for (Everyone,VIP,Moderator,<Rank(name='Weebs')>)
    , is_enabled integer not null
    , is_hidden integer not null
    , primary key (command_id, channel_id)
    , foreign key (command_id) references built_in_command(id)
    , foreign key (channel_id) references channel(id)
);

create table if not exists custom_command (
    id integer primary key
    , channel_id integer not null
    , name text unique not null
    , message text
    , aliases text
    , perms text not null
    , count integer
    , cooldowns text -- e.g.: "3,10,5,0,'Weebs':30" for (Global,Everyone,VIP,Moderator,<Rank(name='Weebs')>)
    , case_sensitive integer not null
    , expire integer
    , expire_action text
    , is_enabled integer not null
    , is_hidden integer not null
    , author_id integer not null
    , modified_by integer not null
    -- , is_builtin integer not null
    , ctime integer not null
    , mtime integer not null
    , foreign key (channel_id) references channel(id)
);

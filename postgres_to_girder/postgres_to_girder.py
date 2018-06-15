import girder_client as gc
import json
import os
import pandas as pd
import psycopg2
import urllib
from datetime import date


def config(
    config_file=None,
    context_file=None
):
    """
    Function to set configuration variables.
    
    Parameters
    ----------
    config_file: string, optional
        path to configuration file
        default = "config.json"
        
    context_file: string, optional
        path to context file
        default = "context.json"
        
    Returns
    -------
    config: dictionary
    
    context: dictionary
    
    api_url: string
    
    Example
    -------
    >>> import json
    >>> config_file = os.path.join(
    ...    os.path.dirname(__file__),
    ...    "config.json.template"
    ... )
    >>> config, context, api_url = config(
    ...     config_file=config_file
    ... )
    >>> config["girder"]["user"]
    'wong'
    """
    if config_file is None:
        config_file = os.path.join(
            os.path.dirname(__file__),
            "config.json"
        ) # pragma: no cover 
    if context_file is None:
        context_file = os.path.join(
            os.path.dirname(__file__),
            "context.json"
        ) # pragma: no cover
    with open (config_file, "r") as j:
        config = json.load(j)
    with open (context_file, "r") as j:
        context = json.load(j)
    api_url = "".join([
        "http://",
        config["girder"]["host"],
        "/api/v1"
    ])
    return(config, context, api_url)
  
  
def connect_to_girder(
    api_url="https://data.kitware.com/api/v1/",
    authentication=None
):
    """
    Function to connect to a Girder DB.
    
    Parameters
    ----------
    api_url: string, optional
        path to running Girder DB API endpoint.
        Default is Kitware Data API
        
    authentication: tuple or string, optional
        (username, password) or APIkey
        (
            username: string
            password: string
        )
        default=None
        
        APIkey: string
            default=None
        
        
    Returns
    -------
    girder_connection: GirderClient
    
    Examples
    --------
    >>> import girder_client as gc
    >>> g = connect_to_girder()
    >>> g.getItem(
    ...     "58cb124c8d777f0aef5d79ff"
    ... )["name"]
    'LARGE_PtCu_NanoParticles-stride-5.html'
    >>> g =connect_to_girder(authentication=("a", "b"))
    Connected to the Girder database 🏗🍃 but could not authenticate.
    >>> g =connect_to_girder(authentication="ab")
    Connected to the Girder database 🏗🍃 but could not authenticate.
    """
    try:
        girder_connection = gc.GirderClient(
            apiUrl=api_url
        ) 
        if authentication:
            if isinstance(
                authentication,
                tuple
            ):
                girder_connection.authenticate(
                    *authentication
                )
            else:
                girder_connection.authenticate(
                    apiKey=authentication
                )
            print(
              "Connected to the Girder database 🏗🍃 and "
              "authenticated."
            ) # pragma: no cover
    except (gc.AuthenticationError, gc.HttpError) as AuthError:
        print(
            "Connected to the Girder database 🏗🍃 but "
            "could not authenticate."
        )
    except:
        print(
            "I am unable to connect to the "
            "Girder database 🏗🍃"
        )
        return(None)
    return(girder_connection)
  
  
def connect_to_postgres(postgres_config):
    """
    Function to connect to a Girder DB.
    
    Parameters
    ----------
    postgres_config: dictionary
        "dbname": string
            Postgres DB name
        "user": string
            Postgres username
        "host": string
            active Postgres IP (no protocol, ie, without "https://")
        "password": string
            password for Postgres user
        
    Returns
    -------
    postgres_connection: connection
        http://initd.org/psycopg/docs/connection.html#connection
    
    Examples
    --------
    >>> config_file = os.path.join(
    ...    os.path.dirname(__file__),
    ...    "config.json.template"
    ... )
    >>> connect_to_postgres(
    ...     config(
    ...         config_file=config_file
    ...     )[0]["postgres"]
    ... )
    I am unable to connect to the Postgres database 🐘
    """
    try:
        postgres_connection = psycopg2.connect(
            " ".join(
                [
                    "=".join([
                        key,
                        postgres_config[
                            key
                        ]
                    ]) for key in postgres_config
                ]
            )
        )
        print("Connected to the Postgres database 🐘") # pragma: no cover 
        return(postgres_connection) # pragma: no cover 
    except (
        psycopg2.OperationalError,
        psycopg2.DatabaseError
    ):
        print(
            "I am unable to connect to the "
            "Postgres database 🐘"
        )
        return(None)
      
      
def get_abbreviation(activity):
    """
    Function to extract abbreviation from
    activity name if one is present
    
    Parameters
    ----------
    activity: string
    
    Returns
    -------
    activity_name: string
    
    abbreviation: string
    
    Example
    -------
    >>> get_abbreviation(
    ...     "Corresponding parts of congruent "
    ...     "triangles are congruent (CPCTC)"
    ... )[1]
    'CPCTC'
    """
    abbreviation = None
    if "(" in activity:
        anames = [
            a.strip(
                ")"
            ).strip() for a in activity.split(
                "("
            )
        ]
        if (
            len(anames)==2
        ):
            if (
                len(anames[0])>len(anames[1])
            ):
                abbreviation = anames[1]
                activity_name = anames[0]
            else:
                abbreviation = anames[0]
                activity_name = anames[1]
        else: # pragma: no cover
            print(anames) # pragma: no cover
    activity_name = activity if not abbreviation else activity_name
    return(
        activity_name,
        abbreviation
    )


def get_girder_id_by_name(
    girder_connection,
    entity,
    name,
    parent=None,
    limit=1,
    sortdir=-1,
    index=0
):
    """
    Function to get the `_id` of a single entity in a Girder database.
    
    Parameters
    ----------
    girder_connection: GirderClient
        an active `GirderClient <http://girder.readthedocs.io/en/latest/python-client.html#girder_client.GirderClient>`_
    
    entity: string
        "collection", "folder", "item", "file", "user"
    
    name: string
        name of entity
        
    parent: 2-tuple, optional, default=None
        (parentType, parent_id)
        parentType: string
            "collection", "folder", or "user"
        parendId: string
            Girder _id for parent
        
    limit: int, optional, default=1
        maximum number of query results
        
    sortdir: int, optional, default=-1
        Sort order: 1 for ascending, -1 for descending.
        
    index: int, default=0
        0-indexed index of named entity in given sort order.
        
    Returns
    -------
    _id: string
        Girder _id of requested entity
        
    Example
    -------
    >>> import girder_client as gc
    >>> get_girder_id_by_name(
    ...     girder_connection=gc.GirderClient(
    ...         apiUrl="https://data.kitware.com/api/v1/"
    ...     ),
    ...     entity="collection",
    ...     name="Cinema",
    ...     parent=None,
    ...     sortdir=1
    ... )
    '55706aa58d777f649a9ba164'
    """
    query = "".join([
        entity,
        "?text=" if entity=="collection" else "?name=",
        name,
        "&parentType={0}&parentId={1}".format(
            *parent
        ) if parent else "",
        "&limit=",
        str(limit),
        "&sortdir=",
        str(sortdir)
    ])
    j = json.loads(
        girder_connection.get(
            query,
            jsonResp=False
        ).content.decode(
            "UTF8"
        )
    )
    return(
        j[0]["_id"] if len(
            j
        ) else None
    )

  
def get_files_in_item(
    girder_connection,
    item_id,
    sort="created",
    sortdir=-1
):
    """
    Function to get a dictionary of Files in an Item in
    a Girder database.
    
    Parameters
    ----------
    girder_connection: GirderClient
        an active `GirderClient <http://girder.readthedocs.io/en/latest/python-client.html#girder_client.GirderClient>`_
    
    item_id: string
        Girder _id of Item.
        
    sort: string, optional
        Field to sort the result set by.
        default = "created"
    
    sortdir: int, optional
        Sort order: 1 for ascending, -1 for descending.
        default = -1
    
    Returns
    -------
    files: dictionary or None
        metadata of files in Girder Item
        
    Example
    -------
    >>> import girder_client as gc
    >>> get_files_in_item(
    ...     girder_connection=gc.GirderClient(
    ...         apiUrl="https://data.kitware.com/api/v1/"
    ...     ),
    ...     item_id="58a372f38d777f0721a64df3"
    ... )[0]["name"]
    'Normal001-T1-Flash.mha'
    """
    return(
      girder_connection.get(
        "".join([
          "item/",
          item_id,
          "/files?",
          "sort=",
          sort,
          "&sortdir=",
          str(sortdir)
        ])
      )
    )
  
  
def get_postgres_item_version(
    activity_name,
    abbreviation=None,
    activity_source=None,
    respondent=None,
    version=None
):
    """
    Function to create an item version in `Mindlogger Item <https://github.com/ChildMindInstitute/mindlogger-app-backend/wiki/Data-Dictionary#activitiesfolderitem>`_ format:
    `[Source] — [Activity] — [Respondent] Report ([Version])`.
    
    Parameters
    ----------
    activity_name: string
    
    abbreviation: string
    
    activity_source: string
    
    respondent: string
    
    version: string
    
    Returns
    -------
    item_version: string
    
    Example
    -------
    >>> activity_name, abbreviation = get_abbreviation(
    ...     "EHQ (Edinburgh Handedness Questionnaire)"
    ... )
    >>> get_postgres_item_version(
    ...     activity_name=activity_name,
    ...     abbreviation=abbreviation,
    ...     activity_source="MATTER Lab",
    ...     respondent="Coworker",
    ...     version="v0.1"
    ... )
    'MATTER Lab ― Edinburgh Handedness Questionnaire (EHQ) ― Coworker Report (v0.1)'
    """
    return(
        "{0}{1}{2}".format(
            "".join([
                activity_source,
                " ― "
            ]) if activity_source else "", # {0}
            "{0}{1}{2}".format(
                activity_name,
                " ({0})".format(
                    abbreviation
                ) if abbreviation else "",
                " ― {0} Report".format(
                        respondent
                    ) if respondent else ""
            ).strip(" "), # {1}
            " ({0})".format(
                version
            ) if version else "" #{2}
        )
    )


def get_user_id_by_email(girder_connection, email):
    """
    Function to get the `_id` of a single User in a Girder database.
    
    Parameters
    ----------
    girder_connection: GirderClient
        an active `GirderClient <http://girder.readthedocs.io/en/latest/python-client.html#girder_client.GirderClient>`_
    
    email: string
        email address
        
    Returns
    -------
    _id: string or None
        Girder _id of requested User, or None if not found
        
    Example
    -------
    >>> import girder_client as gc
    >>> get_user_id_by_email(
    ...     girder_connection=gc.GirderClient(
    ...         apiUrl="https://data.kitware.com/api/v1/"
    ...     ),
    ...     email="test@example.com"
    ... )
    """
    email = email.lower()
    user_ids = [
      user["_id"] for user in girder_connection.get(
            "".join([
                "user?text=",
                email
            ])
        ) if (
            (
                 "email" in user 
            ) and (
                 user["email"]==email
            )
        ) or (
            (
                 "login" in user 
            ) and (
                 user["login"]==email
            )
        )
    ]
    return(
        user_ids[0] if len(user_ids) else None
    )
  
  
def postgres_users_to_girder_users(
    users,
    girder_connection,
    unknown_person={
        "first_name": "Notname",
        "last_name": "Anonymous"
    }
):
    """
    Function to transfer users from Postgres table to
    Girder collection.
    
    Parameters
    ----------
    users: DataFrame
        users table from Postgres DB
        
    girder_connection: GirderClient
        active GirderClient in which to add the users
        
    unknown_person: dictionary
        unknown_person["first_name"]: string
        unknown_person["last_name"]: string
    
    Returns
    -------
    users_by_email: dictionary
        key: string
            email address
        value: string
            Girder User_id
    
    Example
    -------
    >>> import girder_client as gc
    >>> import pandas as pd
    >>> postgres_users_to_girder_users(
    ...     pd.DataFrame(
    ...         {
    ...             'first_name': ['Packages,'],
    ...             'last_name': ['TravisCI'],
    ...             'email': ['travis-packages'],
    ...             'password': [
    ...                 '$2b$12$jchNQFK2jj7UZ/papXfWsu1'
    ...                 '6enEeCUjk2gUxWJ/n6iYPYmejcmNnq'
    ...             ],
    ...             'role': ['user']
    ...         }
    ...     ),
    ...     girder_connection=gc.GirderClient(
    ...         apiUrl="https://data.kitware.com/api/v1/"
    ...     )
    ... )
    {'travis-packages': '55535d828d777f082b592f54'}
    """
    users_by_email = {}
    for i in range(users.shape[0]):
        user_id = get_user_id_by_email(
            girder_connection,
            users.loc[i,"email"]
        )
        if user_id:
            users_by_email[
                users.loc[i,"email"]
            ] = user_id
        else: # pragma: no cover
            users_by_email[
                users.loc[i,"email"]
            ] = girder_connection.post(
                "".join([
                    "user?login=",
                    users.loc[i,"email"].replace(
                        "@",
                        "at"
                    ),
                    "&firstName=",
                    unknown_person[
                        "first_name"
                    ] if not users.loc[
                        i,
                        "first_name"
                    ] else users.loc[
                        i,
                        "first_name"
                    ] if not " " in users.loc[
                        i,
                        "first_name"
                    ] else users.loc[
                        i,
                        "first_name"
                    ].split(" ")[0],
                    "&lastName=",
                    users.loc[
                        i,
                        "last_name"
                    ] if users.loc[
                        i,
                        "last_name"
                    ] else unknown_person[
                        "last_name"
                    ] if not users.loc[
                        i,
                        "first_name"
                    ] else users.loc[
                        i,
                        "first_name"
                    ].split(" ")[1] if " " in users.loc[
                        i,
                        "first_name"
                    ] else users.loc[
                        i,
                        "first_name"
                    ],
                    "&password=",
                    users.loc[i,"password"],
                    "&admin=",
                    "true" if "admin" in str(
                        users.loc[
                            i,
                            "role"
                        ]
                    ) else "false",
                    "&email=",
                    users.loc[
                        i,
                        "email"
                    ]
                ])
            ) # pragma: no cover
    return(users_by_email)
  

def _main():
    """
    Function to execute from commandline to transfer a running
    Postgres DB to a running Girder DB.
    
    "config.json" needs to have its values filled in first.
    """
    # Load configuration
    config, context, api_url = _config() # pragma: no cover
    
    # Connect to Girder
    girder_connection=_connect_to_girder(
        api_url=api_url,
        authentication=(
            config["girder"]["user"],
            config["girder"]["password"]
        )
    ) # pragma: no cover
    
    # Connect to Postgres
    postgres_connection=_connect_to_postgres(
        config["postgres"]
    ) # pragma: no cover
        
    # Get or create activities Collection
    activities_id = get_girder_id_by_name(
        entity="collection",
        name="activities",
        girder_connection=girder_connection
    ) # pragma: no cover
    activities_id = gc.createCollection(
        name="activities",
        public=True
    ) if not activities_id else activities_id # pragma: no cover
    
    # Get tables from Postgres
    postgres_tables = {
        table: pd.io.sql.read_sql_query(
            "SELECT * FROM {0};".format(
                table
            ),
            conn
        ) for table in {
            "acts",
            "users",
            "user_acts",
            "organizations",
            "answers"
        }
    } # pragma: no cover
    
    # Load users into Girder
    users = postgres_users_to_girder_users(
        postgres_tables["users"],
        girder_connection,
        config["missing_persons"]
    ) # pragma: no cover
    
    # Pull respondents out of titles in DataFrame from Postgres
    postgres_tables["acts"] = _respondents(
        postgres_tables["acts"]
    ) # pragma: no cover
    
    
def _respondents(acts):
    """
    Function to extract respondents from 
    activity titles in Postgres table and
    update relevat columns
    
    Parameters
    ----------
    acts: DataFrame
    
    Returns
    -------
    acts: DataFrame
    
    Example
    -------
    >>> import pandas as pd
    >>> _respondents(
    ...     pd.DataFrame(
    ...         {
    ...             "title": [
    ...                 "Test - Self Report",
    ...                 "Test - Parent Report"
    ...             ]
    ...         }
    ...     )
    ... ).loc[0, "respondent"]
    'Self'
    """
    acts["respondent"] = acts["title"].apply(
        lambda x: x.split(
            " - "
        )[
            1
        ].split(
            " "
        )[
            0
        ] if " - " in x else x.split(
            " – "
        )[
            1
        ].split(
            " "
        )[
            0
        ] if " – " in x else x.split(
            "-"
        )[
            1
        ].split(
            " "
        )[
            0
        ] if "Scale-" in x else x.split(
            " ― "
        )[
            1
        ].split(
            "-"
        )[
            0
        ] if "―" in x else x.split(
            "-"
        )[
            1
        ].split(
            ")"
        )[
            0
        ] if "Index-" in x else "Self" if (
            (
                "_SR" in x
            ) or (
                "-SR" in x
            )
        ) else "Parent" if (
            "_P" in x
        ) else ""
    )
    acts["title"] = acts["title"].apply(
        lambda x: x.split(
            " - "
        )[
            0
        ] if " - " in x else x.split(
            " – "
        )[
            0
        ] if " – " in x else x.split(
            "-"
        )[
            0
        ] if "Scale-" in x else x.split(
            " ― "
        )[
            0
        ] if "―" in x else x.split(
            "-"
        )[
            0
        ] if "Index-" in x else x.replace(
            " Self Report",
            ""
        ).replace(
            " Parent Report",
            ""
        )
    ).apply(
        lambda x: "{0})".format(
            x
        ) if (
            "(" in x
        ) and (
            ")"
        ) not in x else x
    )
    return(acts)
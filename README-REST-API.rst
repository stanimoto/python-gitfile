REST API
========

JSON-based API provides a RESTful interface to interact with a git repository.

Structure of the REST URIs
--------------------------

http://<host>:<port>/<repo>/<noun>/<name-or-id>/<path>

Resources
---------

http://<host>:<port>/<repo> is omitted in the following documents.

**GET /blobs/{sha1}**

    Returns a raw content of the blob.

**POST /blobs/**

    Creates a new blob object from the request body and returns the id.

**GET /branches/**

    Returns the list of branches.

**POST /branches/{name}**

    Creates a new branch.
    
    JSON request parameters:
        target - sha1 hex of the target

**DELETE /branches/{name}**

    Deletes a branch.

**GET /branches/{name}/{path}**

    Returns the entry info for the given branch and path.

**POST /branches/{name}/{path}**

    Creates a new entry for the given branch and path.

    JSON request parameters:
        sha1 - sha1 hex of the blob object
        mode - file mode
        author_name - author's name
        author_email - author's email address
        comment - commit message

**PUT /branches/{name}/{path}**

    Replaces the entry for the given branch and path.

    JSON request parameters:
        sha1 - sha1 hex of the blob object
        mode - file mode
        author_name - author's name
        author_email - author's email address
        comment - commit message

**DELETE /branches/{name}/{path}**

    Deletes the entry for the given branch and path.

    JSON request parameters:
        author_name - author's name
        author_email - author's email address
        comment - commit message

**GET /tags/**

    Returns the list of tags.

**POST /tags/{name}**

    Creates a new tag.
    
    JSON request parameters:
        target - sha1 hex of the target

**DELETE /tags/{name}**

    Deletes a tag.

**GET /tags/{name}/{path}**

    Returns the entry info for the given tag and path.

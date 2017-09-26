# XBOS Commissioning

Components involved in an XBOS installation at a site:

## Base BOSSWAVE

- install BOSSWAVE on a server
- create a local git repo for versioning configuration information
- configure namespace:
    - create a namespace key for the site
    - create an alias for the site
    - establish a designated router for the namespace

## Process Management

- configure entity for `spawnd`
- adjust spawnd configuration and deploy spawnd:
    - entity
    - spawnpoint alias ("name")
    - base spawnpoint uri
    - router endpoint

## Driver

- install wizard:
    - choose the device, then fill out the corresponding params file
    - create entity; give it the required permissions:
        - how do we keep track of this?
        - might need to be part of the description of mapping device name to the params.yml file
        - will need to be templated
    - create the archive request; also associated with the device name.
        - will also need to be templated
    - should be able to invoke this

- spawnpoint:
    - need reproducibility; pin to a tag?
    - currently pulls the full container; no caching?
    - better recovery of existing running containers

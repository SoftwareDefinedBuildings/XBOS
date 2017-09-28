######################
### CONFIGURE BOSSWAVE
######################

# name + email address to be attached to configured BOSSWAVE objects
BW2_DEFAULT_CONTACT=

# path to entity to use as an administrative entity for configuring/interacting with services
# Leave blank to have the installer configure this
BW2_DEFAULT_ENTITY=

# path to entity to use for bankrolling BOSSWAVE operations
# Leave blank to have the installer configure this (it will default to $BW2_DEFAULT_ENTITY)
BW2_DEFAULT_BANKROLL=


#######################
### CONFIGURE NAMESPACE
#######################

# set to false to ignore configuration for namespace
CONFIGURE_NAMESPACE=true

# path to entity to use as namespace authority.
# Leave blank to have the installer configure this
NAMESPACE_ENTITY=

# alias to use for the namespace.
# Leave blank to not configure an alias (or use the existing one for your provided NAMESPACE_ENTITY)c
NAMESPACE_ALIAS=

# the VK of the designated router (DR) that  will carry traffic for this namespace
# it is helpful to have the DR ready to make an offer
DESIGNATED_ROUTER_VK=

########################
### CONFIGURE SPAWNPOINT
########################

# if true, install spawnd server
INSTALL_SPAWNPOINT_SERVER=true
# entity to run the spawnd daemon.
# Leave blank to have the installer configure this
SPAWND_ENTITY=
# Spawnpoint system config
SPAWND_MEM_ALLOC="4G"
SPAWND_CPU_SHARES=2048


#######################
### ADDITIONAL INSTALLS
#######################

# if true, install Go 1.9
INSTALL_GO=true

# if true, install spawnctl
# Requires Go
INSTALL_SPAWNPOINT_CLIENT=true

# if true, isntall pundat archiver installation tool
# Requires Go
INSTALL_PUNDAT_CLIENT=true

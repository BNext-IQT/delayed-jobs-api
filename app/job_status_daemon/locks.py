"""
Module that handles the locking system for the status daemons
"""
from app.config import RUN_CONFIG
from app.cache import CACHE

def get_lock_for_lsf_host(lsf_host):
    """
    Returns a lock for a lsf host if it exists
    :param lsf_host: lsf host for which get the lock
    :return: dict with the lock for the lsf_host given as parameter, None if it doesn't exist
    """
    return CACHE.get(key=lsf_host)

def set_lsf_lock(lsf_host, lock_owner):
    """
    Creates a lock on the lsf_host given as parameter in the name of the owner given as parameter, it will expire in the
    time set up in the configuration, set by the value status_agent.lock_validity_seconds
    :param lsf_host: cluster to lock
    :param lock_owner: identifier (normally a hostname) of the process that owns the lock
    """

    seconds_valid = RUN_CONFIG.get('status_agent').get('lock_validity_seconds')
    lock_dict = {
        'owner': lock_owner
    }
    CACHE.set(key=lsf_host, value=lock_dict, timeout=seconds_valid)
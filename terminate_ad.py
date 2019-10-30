import json
import os

import ssl

from ldap3 import Server, Connection, Tls, SUBTREE, ALL

# Include root CA certificate path if you use a self signed AD certificate
SSL_CERT_PATH = "path/to/cert.pem"

# Include the FQDN of your Domain Controller here
FQDN = "ad.example.com"

# Search base is the CN of the container where your users live
search_base='OU=Sites,DC=ad,DC=example,DC=com'

def deprovision_AD(email):
    memberOf_list = []
    ad_info = get_secret("TS/Active-Directory-Offboarding-Info")
    # TODO: Get the into from the secret above and turn into env variables instead
    ad_info_dict = json.loads(ad_info)

    # Binding to AD with latest form of TLS available
    tls_configuration = Tls(ca_certs_file=SSL_CERT_PATH, version=ssl.PROTOCOL_TLS)
    server = Server(FQDN, use_ssl=True, tls=tls_configuration)

    conn = Connection(server, ad_info_dict["sa_username_dn"], ad_info_dict["sa_password"], auto_bind=True,
                      raise_exceptions=True)

    # Find user in AD based off of 'mail' attribute
    search_filter = "(&(objectClass=user)(mail={}))".format(email)
    entry_generator = conn.extend.standard.paged_search(search_base=search_base,
                                                        search_filter=search_filter,
                                                        search_scope=SUBTREE,
                                                        attributes=['memberOf'],
                                                        paged_size=5,
                                                        generator=True)

    for entry in entry_generator:
        dn = entry['dn']
        relative_dn = dn.split(',')[0]
        groups = entry['raw_attributes']['memberOf']
        for group in groups:
            group_str = str(group)
            memberOf_list.append(group_str[2:-1])

    # There is a comment before each offboarding task. Comment out the ones you'd like to skip

    try:
        # Loop through groups and remove user from those groups
        for group in memberOf_list:
            conn.extend.microsoft.remove_members_from_groups(dn, group)

        # Add user to security group
        conn.extend.microsoft.add_members_to_groups(dn, "<dn of new group>")

        # Disable account
        conn.modify(dn, changes={'userAccountControl': (2, '514')})

        # Move to different OU
        conn.modify_dn(dn=dn, relative_dn=relative_dn, new_superior="<dn of new OU>")

        # Delete account
        ## TODO: Figure out the command to delete the AD account

        # Close connection
        conn.unbind()
        return "Success"

    except NameError:
        return "A user with that email address does not exist inside Active Directory"


def __main__():
    # TODO: Figure out how to populate this as an env
    email = input("Please input the departing user's email address: ")
    ad_result = deprovision_AD(email)
    print(ad_result)



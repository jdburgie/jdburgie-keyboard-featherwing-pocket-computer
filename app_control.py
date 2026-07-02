# Shared application controls.
import supervisor


def return_to_menu():
    supervisor.set_next_code_file(None)
    supervisor.reload()

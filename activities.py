import os
import time

import aiohttp
import digitalocean

from temporalio import activity


class DropletActivities:
    def __init__(self, session: aiohttp.ClientSession):
        self.manager = digitalocean.Manager(token=os.environ.get("DIGITALOCEAN_TOKEN"))

    @activity.defn
    async def create_droplet(self, name: str) -> int:
        keys = self.manager.get_all_sshkeys()
        droplet = digitalocean.Droplet(
            token=self.manager.token,
            name=f"{name}-temporal",
            region="sfo3",
            image="ubuntu-24-04-x64",
            size_slug="s-1vcpu-1gb",
            ssh_keys=keys,
            backups=False,
        )
        droplet.create()
        while droplet.ip_address is None:
            time.sleep(1)
            try:
                droplet.load()
            except digitalocean.DataReadError:
                print("{0} waiting to load".format(droplet.name))

        return droplet.id

    @activity.defn
    async def reboot_droplet(self, droplet_id: int) -> str:
        droplet = digitalocean.Droplet(token=self.manager.token, id=droplet_id)
        droplet.power_cycle()

    @activity.defn
    async def terminate_droplet(self, droplet_id: int) -> str:
        droplet = digitalocean.Droplet(token=self.manager.token, id=droplet_id)
        droplet.destroy()

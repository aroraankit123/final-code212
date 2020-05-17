import asyncio

import idom
from idom.core.layout import Layout, LayoutEvent
from idom.core.render import SharedStateRenderer, StopRendering


async def test_shared_state_renderer():
    done = asyncio.Event()
    data_sent_1 = asyncio.Queue()
    data_sent_2 = []

    async def send_1(data):
        await data_sent_1.put(data)

    async def recv_1():
        sent = await data_sent_1.get()

        element_id = sent["root"]
        element_data = sent["new"][element_id]

        if element_data["attributes"]["count"] == 4:
            done.set()
            raise StopRendering()

        target = element_data["eventHandlers"]["anEvent"]["target"]
        return LayoutEvent(target=target, data=[])

    async def send_2(data):
        element_id = data["root"]
        element_data = data["new"][element_id]
        data_sent_2.append(element_data["attributes"]["count"])

    async def recv_2():
        await done.wait()
        raise StopRendering()

    @idom.element
    async def Clickable(self, count=0):
        @idom.event
        async def an_event():
            self.update(count=count + 1)

        return idom.html.div({"anEvent": an_event, "count": count})

    async with SharedStateRenderer(Layout(Clickable())) as renderer:
        await renderer.run(send_1, recv_1, "1")
        await renderer.run(send_2, recv_2, "2")

    assert data_sent_2 == [0, 1, 2, 3, 4]
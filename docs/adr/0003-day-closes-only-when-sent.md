# A workday closes only when a 日报 is sent

The goal is to send a 日报 on every workday. A Run that does not send does not close the day, so a later Run may try again. Already sent is the only normal stop. If today's Upstreams are not ready, the Run stops without sending and without using yesterday's items. If the model fills no mold, a fallback fills molds from the items it already has and pastes those. A broken image is not sent, and a failed webhook does not close the day. We rejected failing the day silent, because that misses workdays for reasons other than "already sent."

# C7413 retained-endpoint repair

Original native pilot37963087457 gains135→134 but rejects two new track_dangling warnings. Five reviewed cuts remain exact; all51140uncut objects survive. The endpoint search adds21B.Cu segments to the original16-segment restoration, no vias or additional cuts. Both anchors are exactly old cut endpoints inside retained copper; synthetic pads exist only in the search. The complete replay is pinned to accepted JR135 d2a7d2c9.

Initial helper assertion correctly rejected an incomplete replay description: the disposable restoration proposal contains no cuts and uses the cut-board hash. The corrected script explicitly combines the original canonical hash and five reviewed cuts from the saved plan. B.Cu search succeeds under the guard in9s; no native acceptance is claimed until the new disposable pilot finishes.

# Atlas v2 cached loss streams

Per-episode 0/1 loss vectors (`l0` incumbent, `l1` challenger, 2000 events per episode) replayed by
`scripts/failure_atlas_v2/run_atlas_v2.py --kind real`. Derived model losses only; no raw features
or labels.

- airlines, bank, criteo, elec2, rialto, spam, weather: byte copies of
  `docs/promising_directions/results/b3/losses/*.npz` (B3 registered real-data run).
- openml_ldpa, uci_occupancy: copied from the B3+ new-case sensitivity work
  (`newcase_losses/` in the `shiftlab-b3-plus-icml` session scratchpad, 2026-11-03); produced by
  that session's chronological train/score pipeline. Not regenerated here.

SHA256 at copy time:

    fcf3a0058a3cc481a0b5a89a89229446edf5dec9ba143ee05e3a4c602f8c7e76  airlines.npz
    3a546964638e031c30c619b33f2b2d724295da80edead210ac1f29639572a164  bank.npz
    bced87ae731827501c131592b6d1fb1da5e9408c92193d450c0fef1b4542417b  criteo.npz
    02c59a22e63dd226297cc39d429fbac5c04cad648d7791834dc8db0fdeabe4a5  elec2.npz
    016bf919209d8081ff1608eadc28ee470609d8c6b56a3bf24c767e5f057dd1e2  openml_ldpa.npz
    92f4cc16aa2168aea1e34952bc9f5ed208bd7dabc32728dcb28f2eb1ca69ba11  rialto.npz
    aebede86f8e5135c45b3694874e01796710b7b714cebaf47ffc79e08bda7ea46  spam.npz
    dd7472f433e1081257c65833244a8ae2509b4e001a499fb4c2cb7b3f1c1aa88f  uci_occupancy.npz
    d06e40a08902209ff48a3850c0d81b3b80ed85caba75670e90ff365d27e388d4  weather.npz

All nine were already exposed to the B3/B3+ programmes. They were not used to develop the Atlas v2
repair (developed on synthetic dev seeds only), but they are not independent of earlier ShiftLab work.

# OBD MOPE fixed-candidate development replay

**Status:** exploratory retrospective development, not real-data confirmation or a valid-data guarantee.

The training-selected position-1 item was `41`. The held-forward segment contains 274,737 position-1 records over 2019-11-27 through 2019-11-30. Its IPW candidate-minus-Random click-value estimate is `0.00180900`. MOPE's lower bound first crossed zero at event `None`; its first empty set was `866`. The fixed-horizon Hoeffding lower bound is `-0.18498714` and promoted is `False`.

The OBD unit/dependence, slate-interference, feature timing and label-release contracts remain unresolved. Accordingly, neither the MOPE nor Hoeffding guarantee is asserted for this replay. See the frozen protocol and aggregate manifest for the exact scope and provenance.

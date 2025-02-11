"""Electronic structure results view widgets"""
import json
import random

import ipywidgets as ipw
from aiida import orm
from monty.json import jsanitize
from widget_bandsplot import BandsPlotWidget

from aiidalab_qe.common.panel import ResultPanel


def export_data(work_chain_node, group_dos_by="atom"):
    dos = export_pdos_data(work_chain_node, group_dos_by=group_dos_by)
    fermi_energy = dos["fermi_energy"] if dos else None

    bands = export_bands_data(work_chain_node, fermi_energy)

    return dict(
        bands=bands,
        dos=dos,
    )


def export_pdos_data(work_chain_node, group_dos_by="atom"):
    if "pdos" in work_chain_node.outputs:
        _, energy_dos, _ = work_chain_node.outputs.pdos.dos.output_dos.get_x()
        tdos_values = {
            f"{n}": v for n, v, _ in work_chain_node.outputs.pdos.dos.output_dos.get_y()
        }

        dos = []

        if "projections" in work_chain_node.outputs.pdos.projwfc:
            # The total dos parsed
            tdos = {
                "label": "Total DOS",
                "x": energy_dos.tolist(),
                "y": tdos_values.get("dos").tolist(),
                "borderColor": "#8A8A8A",  # dark gray
                "backgroundColor": "#999999",  # light gray
                "backgroundAlpha": "40%",
                "lineStyle": "solid",
            }
            dos.append(tdos)

            dos += _projections_curated(
                work_chain_node.outputs.pdos.projwfc.projections,
                group_dos_by=group_dos_by,
                spin_type="none",
            )

        else:
            # The total dos parsed
            tdos_up = {
                "label": "Total DOS (↑)",
                "x": energy_dos.tolist(),
                "y": tdos_values.get("dos_spin_up").tolist(),
                "borderColor": "#8A8A8A",  # dark gray
                "backgroundColor": "#999999",  # light gray
                "backgroundAlpha": "40%",
                "lineStyle": "solid",
            }
            tdos_down = {
                "label": "Total DOS (↓)",
                "x": energy_dos.tolist(),
                "y": (-tdos_values.get("dos_spin_down")).tolist(),  # minus
                "borderColor": "#8A8A8A",  # dark gray
                "backgroundColor": "#999999",  # light gray
                "backgroundAlpha": "40%",
                "lineStyle": "dash",
            }
            dos += [tdos_up, tdos_down]

            # spin-up (↑)
            dos += _projections_curated(
                work_chain_node.outputs.pdos.projwfc.projections_up,
                group_dos_by=group_dos_by,
                spin_type="up",
            )

            # spin-dn (↓)
            dos += _projections_curated(
                work_chain_node.outputs.pdos.projwfc.projections_down,
                group_dos_by=group_dos_by,
                spin_type="down",
                line_style="dash",
            )

        data_dict = {
            "fermi_energy": work_chain_node.outputs.pdos.nscf.output_parameters[
                "fermi_energy"
            ],
            "dos": dos,
        }

        return json.loads(json.dumps(data_dict))

    else:
        return None


def export_bands_data(work_chain_node, fermi_energy=None):
    if "bands" in work_chain_node.outputs:
        data = json.loads(
            work_chain_node.outputs.bands.band_structure._exportcontent(
                "json", comments=False
            )[0]
        )
        # The fermi energy from band calculation is not robust.
        data["fermi_level"] = (
            fermi_energy
            or work_chain_node.outputs.bands.band_parameters["fermi_energy"]
        )
        return [
            jsanitize(data),
        ]
    else:
        return None


def _projections_curated(
    projections: orm.ProjectionData,
    group_dos_by="atom",
    spin_type="none",
    line_style="solid",
):
    """Collect the data from ProjectionData and parse it as dos list which can be
    understand by bandsplot widget. `group_dos_by` is for which tag to be grouped, by atom or by orbital name.
    The spin_type is used to invert all the y values of pdos to be shown as spin down pdos and to set label.
    """
    _pdos = {}

    for orbital, pdos, energy in projections.get_pdos():
        orbital_data = orbital.get_orbital_dict()
        kind_name = orbital_data["kind_name"]
        atom_position = [round(i, 2) for i in orbital_data["position"]]
        orbital_name = orbital.get_name_from_quantum_numbers(
            orbital_data["angular_momentum"], orbital_data["magnetic_number"]
        ).lower()

        if group_dos_by == "atom":
            dos_group_name = atom_position
        elif group_dos_by == "angular":
            # by orbital label
            dos_group_name = orbital_name[0]
        elif group_dos_by == "angular_and_magnetic":
            # by orbital label
            dos_group_name = orbital_name
        else:
            raise Exception(f"Unknow dos type: {group_dos_by}!")

        key = f"{kind_name}-{dos_group_name}"
        if key in _pdos:
            _pdos[key][1] += pdos
        else:
            _pdos[key] = [energy, pdos]

    dos = []
    for label, (energy, pdos) in _pdos.items():
        if spin_type == "down":
            # invert y-axis
            pdos = -pdos
            label = f"{label} (↓)"

        if spin_type == "up":
            label = f"{label} (↑)"

        orbital_pdos = {
            "label": label,
            "x": energy.tolist(),
            "y": pdos.tolist(),
            "borderColor": cmap(label),
            "lineStyle": line_style,
        }
        dos.append(orbital_pdos)

    return dos


def cmap(label: str) -> str:
    """Return RGB string of color for given pseudo info
    Hardcoded at the momment.
    """
    # if a unknow type generate random color based on ascii sum
    ascn = sum([ord(c) for c in label])
    random.seed(ascn)

    return "#%06x" % random.randint(0, 0xFFFFFF)


class Result(ResultPanel):
    title = "Electronic Structure"
    workchain_labels = ["bands", "pdos"]

    def __init__(self, node=None, **kwargs):
        self.dos_group_label = ipw.Label(
            "DOS grouped by:",
            layout=ipw.Layout(justify_content="flex-start", width="120px"),
        )
        self.group_dos_by = ipw.ToggleButtons(
            options=[
                ("Atom", "atom"),
                ("Orbital", "angular"),
            ],
            value="atom",
        )
        self.settings = ipw.HBox(
            children=[
                self.dos_group_label,
                self.group_dos_by,
            ],
            layout={"margin": "0 0 30px 30px"},
        )
        self.group_dos_by.observe(self._observe_group_dos_by, names="value")
        super().__init__(node=node, **kwargs)

    def _observe_group_dos_by(self, change):
        """Update the view of the widget when the group_dos_by value changes."""
        self._update_view()

    def _update_view(self):
        """Update the view of the widget."""
        #
        data = export_data(self.node, group_dos_by=self.group_dos_by.value)
        _bands_plot_view = BandsPlotWidget(
            bands=data.get("bands", None),
            dos=data.get("dos", None),
        )
        # update the electronic structure tab
        self.children = [
            self.settings,
            _bands_plot_view,
        ]

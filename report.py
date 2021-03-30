from aiida.common.exceptions import NotExistentAttributeError

FUNCTIONAL_LINK_MAP = {
    "PBE": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.77.3865",
    "PBEsol": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.100.136406",
}

PSEUDO_LINK_MAP = {"SSSP": "https://www.materialscloud.org/discover/sssp/table"}


def generate_report_dict(qeapp_wc):
    """Generate a dictionary for reporting the inputs for the `QeAppWorkChain`"""

    pseudo_family = qeapp_wc.get_extra("builder_parameters", {}).get(
        "pseudo_family", None
    )
    if pseudo_family is None:
        raise ValueError(
            "No `pseudo_family` found in the `builder_parameters` of the extras set on the work chain."
        )

    pseudo_family_list = pseudo_family.split("/")
    pseudo_library = pseudo_family_list[0]

    if pseudo_library == "SSSP":
        pseudo_version = pseudo_family_list[1]
        functional = pseudo_family_list[2]
        pseudo_protocol = pseudo_family_list[3]
    else:
        raise NotImplementedError

    energy_cutoffs = None
    scf_kpoints_distance = None
    bands_kpoints_distance = None
    nscf_kpoints_distance = None

    for work_chain in qeapp_wc.called:

        if energy_cutoffs is None:
            try:
                parameters = work_chain.inputs.base__pw__parameters.get_dict()
                energy_cutoffs = {
                    "ecutwfc": parameters["SYSTEM"]["ecutwfc"],
                    "ecutrho": parameters["SYSTEM"]["ecutrho"],
                }
            except NotExistentAttributeError:
                pass

        if scf_kpoints_distance is None:
            try:
                scf_kpoints_distance = work_chain.inputs.base__kpoints_distance.value
            except NotExistentAttributeError:
                pass
            try:
                scf_kpoints_distance = work_chain.inputs.scf__kpoints_distance.value
            except NotExistentAttributeError:
                pass

        if bands_kpoints_distance is None:
            try:
                bands_kpoints_distance = work_chain.inputs.bands_kpoints_distance.value
            except NotExistentAttributeError:
                pass

        if nscf_kpoints_distance is None:
            try:
                nscf_kpoints_distance = work_chain.inputs.nscf__kpoints_distance.value
            except NotExistentAttributeError:
                pass

    report_dict = {
        "Functional": (functional, FUNCTIONAL_LINK_MAP[functional]),
        "Pseudopotential library": (
            f"{pseudo_library} {pseudo_protocol} v{pseudo_version}",
            f"{PSEUDO_LINK_MAP[pseudo_library]}/{pseudo_protocol}",
        ),
        "Plane wave energy cutoff (wave functions)": (energy_cutoffs["ecutwfc"], None),
        "Plane wave energy cutoff (charge density)": (energy_cutoffs["ecutrho"], None),
    }
    if scf_kpoints_distance is not None:
        report_dict["K-point mesh distance (SCF)"] = (scf_kpoints_distance, None)
    if nscf_kpoints_distance is not None:
        report_dict["K-point mesh distance (NSCF)"] = (nscf_kpoints_distance, None)
    if bands_kpoints_distance is not None:
        report_dict["K-point mesh distance (Bands)"] = (bands_kpoints_distance, None)

    return report_dict


FUNCTIONAL_REPORT_MAP = {
    "LDA": "local density approximation (LDA)",
    "PBE": "generalized gradient approximation of Perdew-Burke-Ernzerhof (PBE)",
    "PBEsol": "the revised generalized gradient approximation of Perdew-Burke-Ernzerhof (PBE) for solids",
}


def generate_report_text(report_dict):
    """Generate a text for reporting the inputs for the `QeAppWorkChain`

    :param report_dict: dictionary generated by the `generate_report_dict` function.
    """

    report_string = (
        "All calculations are performed within the density-functional "
        "theory formalism as implemented in the Quantum ESPRESSO code. "
        "The pseudopotential for each element is extracted from the "
        f'{report_dict["Pseudopotential library"][0]} '
        "library. The wave functions "
        "of the valence electrons are expanded in a plane wave basis set, using an "
        "energy cutoff equal to "
        f'{round(report_dict["Plane wave energy cutoff (wave functions)"][0])} Ry '
        "for the wave functions and "
        f'{round(report_dict["Plane wave energy cutoff (charge density)"][0])} Ry '
        "for the charge density and potential. "
        "The exchange-correlation energy is "
        "calculated using the "
        f'{FUNCTIONAL_REPORT_MAP[report_dict["Functional"][0]]}. '
        "A Monkhorst-Pack mesh is used for sampling the Brillouin zone, where the "
        "distance between the k-points is set to "
    )
    kpoints_distances = []
    kpoints_calculations = []

    for calc in ("SCF", "NSCF", "Bands"):
        if f"K-point mesh distance ({calc})" in report_dict:
            kpoints_distances.append(
                str(report_dict[f"K-point mesh distance ({calc})"][0])
            )
            kpoints_calculations.append(calc)

    report_string += ", ".join(kpoints_distances)
    report_string += " for the "
    report_string += ", ".join(kpoints_calculations)
    report_string += " calculation"
    if len(kpoints_distances) > 1:
        report_string += "s, respectively"
    report_string += "."

    return report_string

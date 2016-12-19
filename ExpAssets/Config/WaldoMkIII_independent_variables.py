__author__ = 'jono'
from klibs.KLIndependentVariable import IndependentVariableSet, IndependentVariable

WaldoMkIII_ind_vars = IndependentVariableSet()
WaldoMkIII_ind_vars.add_variable("bg_image", str, ("wally_01", "wally_02", "wally_03", "wally_04", "wally_05", "wally_06",
								  "wally_07", "wally_08", "wally_09"))
WaldoMkIII_ind_vars.add_variable("angle", int, (0,60,120,180,240,300))
WaldoMkIII_ind_vars.add_variable("target_count", int, (1,2))
WaldoMkIII_ind_vars.add_variable("bg_state", str, ("present", "absent", "intermittent"))
WaldoMkIII_ind_vars.add_variable("n_back", int, (1,2))

# WaldoMkIII_ind_vars["bg_image"].add_values("wally_01", "wally_02", "wally_03", "wally_04", "wally_05", "wally_06",
# 										   "wally_07", "wally_08", "wally_09")
# WaldoMkIII_ind_vars["angle"].add_values(0,60,120,180,240,300)
# WaldoMkIII_ind_vars["target_count"].add_values(1,2)
# WaldoMkIII_ind_vars["bg_state"].add_values("present", "absent", "intermittent")
# WaldoMkIII_ind_vars["n_back"].add_values(1,2)

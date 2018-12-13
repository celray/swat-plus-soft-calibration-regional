'''
this script performs soft calibration per region

Author      : Celray James CHAWANDA
Institution : VUB
Contact     : celray.chawanda@outlook.com
'''
# import requirements
import os
import sys
import random
import time
import copy

# functions
def write_to(filename, string):
    """
    function to write string to file
    """
    fl = open(filename, "w")
    fl.write(string)
    fl.close()


def read_from(filename):
    """
    function to read from file; lines are lists
    """
    fl = open(filename, "r")
    raw = fl.readlines()
    fl.close()
    return raw


def run_in_dir_with_update(txtinout_dir_, executable="rev55_64rel.exe", final_line="Execution successfully completed", running=False):
    """
    changes to directory and runs a program providing updates and returns to previous directory
    """
    current_dir = os.getcwd()

    new_dir = txtinout_dir_
    os.chdir(new_dir)
    try:
        os.remove("tmp_log_file.txt")
    except:
        pass
    ended = False
    while True:
        if not running == True:
            running = True
            os.system("START /B " + executable + " > tmp_log_file.txt")
        else:
            try:
                lines = read_from("tmp_log_file.txt")
                if final_line.lower().replace(" ", "") == lines[-1].strip('\n').lower().replace(" ", ""):
                    if not ended == True:
                        ended = True
                        print("\n\t " + lines[-1].strip("   Original Simulation    ").strip('\n') + "\n").replace("  Exec", "Exec")
                    time.sleep(1)
                    os.remove("tmp_log_file.txt")
                    os.chdir(current_dir)
                    return

                sys.stdout.write("\r\t\t\t\t\t\t\t\t\t\t\t\t")
                sys.stdout.flush()
                sys.stdout.write("\r\t    " + lines[-1].strip('\n').replace(" Original Simulation    ", "").replace(" reading", "reading"))
                sys.stdout.flush()
            except:
                pass
    os.chdir(current_dir)



def os_string(input_string):
    '''
    this function removes extra spaces in the string if there is more than one between characters
    '''
    for t in range(0, 20):
        input_string = input_string.replace("  ", " ")
    return input_string


def get_txtinout_ratios(txt_dir, tr_index, r_hru_members, r_hru_areas):
    _aa_pr = 0
    _aa_et = 0
    _aa_sr = 0
    _aa_total_area = 0

    weighing_areas = {}

    # get area for region
    for hru_member in r_hru_members[str(tr_index)]:
        for sub_hru in range(int(str(hru_member[0])), int(str(hru_member[1].strip("-"))) + 1):
            _aa_total_area += r_hru_areas[str(sub_hru)]

    # get hru read values
    wb_hru_aa_content = read_from("{txt}/waterbal_aa_hru.txt".format(txt = txt_dir))
    all_hru_aa = {}
    for wa_line in wb_hru_aa_content:
        if wa_line == wb_hru_aa_content[0]:
            continue
        if wa_line == wb_hru_aa_content[1]:
            continue
        all_hru_aa[os_string(wa_line).split(" ")[5]] = aa_hru(float(os_string(wa_line).split(" ")[8]))
        all_hru_aa[os_string(wa_line).split(" ")[5]].sr = float(os_string(wa_line).split(" ")[11])
        all_hru_aa[os_string(wa_line).split(" ")[5]].et = float(os_string(wa_line).split(" ")[15])

    # weight average et, sr and pr
    for we_hru_member in r_hru_members[str(tr_index)]:
        for we_sub_hru in range(int(str(we_hru_member[0])), int(str(we_hru_member[1].strip("-"))) + 1):
            _aa_pr += (all_hru_aa[str(we_sub_hru)].pr * (r_hru_areas[str(we_sub_hru)]/_aa_total_area))
            _aa_et += (all_hru_aa[str(we_sub_hru)].et * (r_hru_areas[str(we_sub_hru)]/_aa_total_area))
            _aa_sr += (all_hru_aa[str(we_sub_hru)].sr * (r_hru_areas[str(we_sub_hru)]/_aa_total_area))

    # return ratios
    returned_ratios = ratio()
    returned_ratios.precip = _aa_pr
    returned_ratios.et_v = _aa_et
    returned_ratios.sr_v = _aa_sr
    returned_ratios.gw_v = _aa_pr - _aa_et - _aa_sr

    returned_ratios.get_ratios()
    return returned_ratios


def report(string_, main = False, before = False, after = False):
    if before:
        print("\t{st}".format(st = "-" * 80))
    if main:
        print("\t> {st}".format(st = string_))
    else:
        print("\t  > {st}".format(st = string_))
    if after:
        print("\t{st}".format(st = "-" * 80))
    
def get_difference(txt_ratios, obj_ratios, par_):
    delta = None
    try:
        if par_.ratio_type == "sr_r":
            delta = obj_ratios.sr_v - txt_ratios.sr_v
        if par_.ratio_type == "et_r":
            delta = obj_ratios.et_v - txt_ratios.et_v
        if par_.ratio_type == "gw_r":
            delta = obj_ratios.gw_v - txt_ratios.gw_v
    except:
        pass
    return delta

def apply_parameters(region_pars, txt_dir, zero = False):
    region_lsu_objects = {}             # initialise dictionary to store lsu member information for region
    region_hru_objects = {}             # initialise dictionary to store hru member information for region
    region_hru_members = {}             # holds lenght and member lists formated for calibration.cal file
    lsu_def = {}                        # keeps all info on elements of lsus

    # fill region_lsu_objects dictionary
    lsu_element_content = read_from("{0}/region_ls_ele.cal".format(txt_dir))
    for rle_index in range(1, len(region_pars) + 1):
        for re_line in lsu_element_content:
            if str(rle_index) == os_string(re_line).split(" ")[0]:
                region_lsu_objects[str(rle_index)] = os_string(re_line.strip("\n")).split(" ")[3:]
                try:
                    region_lsu_objects[str(rle_index)].remove('') #removing any items resulting from spaces at the end
                except:
                    pass
                # print("{0}: length: {2} members: {1}".format(rle_index, region_lsu_objects[str(rle_index)], len(region_lsu_objects[str(rle_index)])))
                break

    # use member information for lsu to get hrus from connection file
    # fill lsu_def dictionary
    lsu_def_content = read_from("{dir}/ls_unit.def".format(dir = txt_dir))
    for lsu_def_line in lsu_def_content:
        if lsu_def_line == lsu_def_content[0]:
            continue
        if lsu_def_line == lsu_def_content[1]:
            continue
        lsu_def[os_string(lsu_def_line).split(" ")[1]] = [os_string(lsu_def_line).split(" ")[5], os_string(lsu_def_line).split(" ")[6]]

    # fill region_hru_objects dictionary
    for rhe_index in range(1, len(region_pars) + 1):
        region_hru_objects[str(rhe_index)] = []
        for region_member in region_lsu_objects[str(rhe_index)]:
            region_hru_objects[str(rhe_index)].append(lsu_def[region_member])
    
    # create final strings for calibration.cal file
    for rhm_index in range(1, len(region_pars) + 1):
        region_hru_members[str(rhm_index)] = cal_line()
        region_hru_members[str(rhm_index)].get_properties(region_hru_objects[str(rhm_index)])

    # create calibration.cal file
    calibration_cal = "calibration.cal for soft data calibration\n  {cc_line_count}\nNAME           CHG_TYP                  VAL   CONDS  LYR1   LYR2  YEAR1  YEAR2   DAY1   DAY2  OBJ_TOT\n"

    cal_line_count = 0
    for cal_index in range(1, len(region_pars) + 1):
        for cc_par in region_pars[str(cal_index)]:
            calibration_cal += "{cc_parname}{cc_chg_typ}{cc_par_value}{cc_conds}     0      0      0      0      0      0{cc_obj_tot}{cc_ele}\n".format(
                cc_parname      = cc_par.par_name.ljust(11), 
                cc_chg_typ      = cc_par.chg_type.rjust(11),
                cc_par_value    = "{0:.3f}".format(cc_par.value).rjust(22),
                cc_conds        = str(0).rjust(7),       # str(region_hru_members[str(cal_index)].conds).rjust(7),
                cc_obj_tot      = str(region_hru_members[str(cal_index)].objs).rjust(9),
                cc_ele          = region_hru_members[str(cal_index)].string
            )
            cal_line_count += 1
    
    write_to("{dir}/calibration.cal".format(dir = txt_dir), calibration_cal.format(cc_line_count = cal_line_count))
    return region_hru_objects

def get_x_intercept(point_1, point_2):
    if (point_2.x-point_1.x) == 0:
        m = "infinity"
        y_int = None
        x_int = None
    else:
        m = float((point_2.y-point_1.y))/(point_2.x-point_1.x)
        y_int = point_1.y - (m*point_1.x)   
        if float((point_2.y-point_1.y)) == 0:
            x_int = None
        else:
            x_int = float(0 - y_int)/m
    return x_int

def get_actual_component(chg_typ):
    if chg_typ == 'sr_r':
        return 'surface runoff'
    if chg_typ == 'et_r':
        return 'evapotranspiration'
    if chg_typ == 'gw_r':
        return 'ground water'


# classes

class cal_line:
    '''
    holds properties of a calibration.cal line
    '''
    def __init__(self):
        self.string = ""
        self.conds = 0
        self.objs = 0
    
    def get_properties(self, rh_objects):
        for element in rh_objects:
            self.string += element[0].rjust(8) + element[1].rjust(8)
            self.conds += (0 - int(element[1]) - int(element[0]) + 1)
            self.objs += 2

class parameter:
    '''
    class to hold all parameter object properties
    '''
    def __init__(self, name, chg_type, r_):
        self.par_name = name
        self.chg_type = chg_type
        self.set_bound_u = None
        self.set_bound_l = None
        self.l_limit = None
        self.u_limit = None
        self.value = 0              # 0.1 * 0.1 * random.random()
        self.ratio_type = r_

    def get_properties(self, property_file):
        property_content = read_from(property_file)
        for pc_line in property_content:
            if os_string(pc_line).split(" ")[0] == self.par_name:
                self.set_bound_l    = float(os_string(pc_line).split(" ")[2])
                self.set_bound_u    = float(os_string(pc_line).split(" ")[3])
                self.l_limit        = float(os_string(pc_line).split(" ")[4])
                self.u_limit        = float(os_string(pc_line).split(" ")[5])
        
class ratio:
    def __init__(self):
        self.name = None
        self.precip = None
        self.et_r = None
        self.gw_r = None
        self.sr_r = None
        self.et_v = None
        self.gw_v = None
        self.sr_v = None

    def get_values(self):
        self.et_v = (self.precip * self.et_r) if (not self.et_r == "-") else None
        self.gw_v = (self.precip * self.gw_r) if (not self.gw_r == "-") else None
        self.sr_v = (self.precip * self.sr_r) if (not self.sr_r == "-") else None

    def get_ratios(self):
        self.et_r = (self.et_v / self.precip) if not (self.et_v is None) else None
        self.gw_r = (self.gw_v / self.precip) if not (self.gw_v is None) else None
        self.sr_r = (self.sr_v / self.precip) if not (self.sr_v is None) else None

class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class aa_hru:
    def __init__(self, precip):
        self.pr = precip
        self.sr = None
        self.et = None


# initialise

report("initialising variables", main = True, before = True)
txtinout_dir = "txtinout"               # directory where the model runs

history_parameters = {}                 # history parameters
current_parameters = {}                 # current parameters
history_components = {}                 # for history differences
current_differences = {}                # current differences
history_differences = {}                # history differences

current_ratios = {}                     # the current state of ratios and component values being adjusted
objective_ratios = {}                   # target ratios

region_hrus = None                      # returned when applying parameters
region_precipitation = {}
hru_areas = {}                          # needed for weighted mean when finding differences and ratios
region_count = None
'''
# parameters you can use
parameter("cn2", "abschg", "sr_r")      
parameter("epco", "abschg", "et_r")
parameter("esco", "abschg", "et_r")
parameter("lat_len", "pctchg", "gw_r")
parameter("k_lo", "abschg", "et_r")
parameter("slope", "abschg", "et_r")
parameter("tconc", "abschg", "sr_r")
parameter("perco", "abschg", "gw_r")
parameter("cn3_swf", "abschg", "sr_r")
parameter("dep_imp", "abschg", "gw_r")
parameter("revapc", "abschg", "et_r")
parameter("etco", "abschg", "et_r")
'''

# read wanted ratios
region_codes_content = read_from("{0}/region_codes.cal".format(txtinout_dir))
region_count = int(region_codes_content[1].split("  ")[0].strip(" "))

for rc_index in range(1, region_count + 1):
    objective_ratios[str(rc_index)]         = ratio()          # create instance and set values ( +1 to start on the third line)
    objective_ratios[str(rc_index)].et_r    = float(os_string(region_codes_content[rc_index + 1]).split(" ")[2]) if not os_string(region_codes_content[rc_index + 1]).split(" ")[2] == "-" else os_string(region_codes_content[rc_index + 1]).split(" ")[2]
    objective_ratios[str(rc_index)].sr_r    = float(os_string(region_codes_content[rc_index + 1]).split(" ")[3]) if not os_string(region_codes_content[rc_index + 1]).split(" ")[3] == "-" else os_string(region_codes_content[rc_index + 1]).split(" ")[3]
    objective_ratios[str(rc_index)].gw_r    = float(os_string(region_codes_content[rc_index + 1]).split(" ")[4]) if not os_string(region_codes_content[rc_index + 1]).split(" ")[4] == "-" else os_string(region_codes_content[rc_index + 1]).split(" ")[4]

# read parameters and properties
for cp_index in range(1, region_count + 1):
    current_parameters[str(cp_index)] = [parameter("cn2", "pctchg", "sr_r"), parameter("esco", "pctchg", "et_r")] #, parameter("epco", "abschg", "et_r")]
    for par_object in current_parameters[str(cp_index)]:
        par_object.get_properties("{txt_dir}/ls_parms.cal".format(txt_dir = txtinout_dir))

# find default differences (for zero parameters)
report("calulating default water balance components - running swat plus\n")
region_hrus = apply_parameters(current_parameters, txtinout_dir, True)      # get hrus for each region and applu parameters

run_in_dir_with_update(txtinout_dir)                                        # running swat plus for default performance

hru_con_content = read_from("{txt_dir}/hru.con".format(txt_dir = txtinout_dir))
for hc_line in hru_con_content:                                             # get areas for hrus
    if hc_line == hru_con_content[0]:
        continue
    if hc_line == hru_con_content[1]:
        continue
    hru_areas[os_string(hc_line).split(" ")[1]] = float(os_string(hc_line).split(" ")[4])

for cr_index in range(1, region_count + 1):                                 # get current ratios and precipitation for each region
    current_ratios[str(cr_index)] = ratio()

for curr_ratios_index in range(1, region_count + 1):
    current_ratios[str(curr_ratios_index)] = get_txtinout_ratios(txtinout_dir, curr_ratios_index, region_hrus, hru_areas)
    objective_ratios[str(curr_ratios_index)].precip = copy.deepcopy(current_ratios[str(curr_ratios_index)].precip)
    objective_ratios[str(curr_ratios_index)].get_values()


# set maximum number of iterations
iteration_count = 200
minimum_difference = 4

report("maximum iterations: {it_n}".format(it_n = iteration_count), main = True)

sc_string = "region     components    objective_ratios   initial_ratios    sc_ratios\r\n"

for sc_str_index in range(1, region_count + 1):
    sc_string += "{rgn}".format(rgn = sc_str_index).rjust(6) + "sr_r".rjust(15) + str(objective_ratios[str(sc_str_index)].sr_r).rjust(20) + "" + "ini_sr{o}".format(o = sc_str_index) + "" + "" + "sc_sr{o}".format(o = sc_str_index) + "\n"
    sc_string += "{rgn}".format(rgn = "").rjust(6) + "et_r".rjust(15) + str(objective_ratios[str(sc_str_index)].et_r).rjust(20) + "" + "ini_et{o}".format(o = sc_str_index) + "" + "" + "sc_et{o}".format(o = sc_str_index) + "\n"
    sc_string += "{rgn}".format(rgn = "").rjust(6) + "gw_r".rjust(15) + str(objective_ratios[str(sc_str_index)].gw_r).rjust(20) + "" + "ini_gw{o}".format(o = sc_str_index) + "" + "" + "sc_gw{o}".format(o = sc_str_index) + "\n\n"

for sc_str_index in range(1, region_count + 1):
    sc_string = sc_string.replace("ini_sr{z}".format(z = sc_str_index), "{sr_kw}")
    sc_string = sc_string.format(sr_kw = str(round(current_ratios[str(sc_str_index)].sr_r, 3)).rjust(17))
    sc_string = sc_string.replace("ini_et{z}".format(z = sc_str_index), "{et_kw}")
    sc_string = sc_string.format(et_kw = str(round(current_ratios[str(sc_str_index)].et_r, 3)).rjust(17))
    sc_string = sc_string.replace("ini_gw{z}".format(z = sc_str_index), "{gw_kw}")
    sc_string = sc_string.format(gw_kw = str(round(current_ratios[str(sc_str_index)].gw_r, 3)).rjust(17))

# main loop
for par_index in range(0, len(current_parameters["1"])):    # calibrate parameter by parameter
    # add to history parameters and historry components
    for ah_index in range(1, region_count + 1):
        history_differences[str(ah_index)] = []
        history_components[str(ah_index)] = []
        history_parameters[str(ah_index)] = []
        history_components[str(ah_index)].append(copy.deepcopy(current_ratios))
        history_parameters[str(ah_index)].append(copy.deepcopy(current_parameters))

    under_calibration = {}
    for uc_index in range(1, region_count + 1):
        under_calibration[str(uc_index)] = None
        if uc_index == 1:
            under_calibration[str(uc_index)] = True
        else:
            under_calibration[str(uc_index)] = False

    report("calibrating {pr_n}".format(pr_n = current_parameters["1"][par_index].par_name), before = True, main = True)
    x_intercept = {}
    for xi_index in range(1, region_count + 1):
        x_intercept[str(xi_index)] = None
    current_iteration = 0

    for iteration in range(1, iteration_count + 1):         # do for the entire number of iterations
        current_iteration += 1
        report("iteration {cur_it} of a maximum of {it_n}".format(
            it_n    = iteration_count,
            cur_it  = current_iteration
        ))
        # propose new parameters if first time, else, get from learned behaviour in x_intercept dictionary
        for np_index in range(1, region_count + 1):
            if under_calibration[str(np_index)]:
                if len(history_differences[str(np_index)]) < 1:
                    history_differences[str(np_index)].append(copy.deepcopy(get_difference(current_ratios[str(np_index)], objective_ratios[str(np_index)], current_parameters[str(np_index)][par_index])))
                    # check if the component for this parameter is being calibrated and move on if not
                    if history_differences[str(np_index)][-1] is None:
                        history_differences[str(np_index)] = []
                        under_calibration[str(np_index)] = False
                        try:
                            under_calibration[str(np_index + 1)] = True
                            actual_component = get_actual_component(current_parameters[str(np_index)][par_index].ratio_type)
                            report("the {act_c} component will not be calibrated for the region {rgn_1},\n\t    no ratio specified in region_codes.cal, proceeding to next region".format(act_c = actual_component, rgn_1 = np_index), after = True)
                            continue
                        except:
                            pass

                    if current_parameters[str(np_index)][par_index].par_name == "cn2":
                        current_parameters[str(np_index)][par_index].value = ((current_parameters[str(np_index)][par_index].set_bound_u - current_parameters[str(np_index)][par_index].value) * random.random() * 0.3) + ((current_parameters[str(np_index)][par_index].set_bound_u - current_parameters[str(np_index)][par_index].value)/3 * 0.7)
                    else:
                        current_parameters[str(np_index)][par_index].value = (current_parameters[str(np_index)][par_index].set_bound_u - current_parameters[str(np_index)][par_index].value)/2

                # check limits and bounds
                if current_parameters[str(np_index)][par_index].value > current_parameters[str(np_index)][par_index].set_bound_u:
                    current_parameters[str(np_index)][par_index].value = current_parameters[str(np_index)][par_index].set_bound_u
                if current_parameters[str(np_index)][par_index].value < current_parameters[str(np_index)][par_index].set_bound_l:
                    current_parameters[str(np_index)][par_index].value = current_parameters[str(np_index)][par_index].set_bound_l
        
        # apply parameters
        report("applying parameters")
        apply_parameters(current_parameters, txtinout_dir)

        # run swat plus
        report("running swatplus")
        run_in_dir_with_update(txtinout_dir)

        for curr_ratios_update_index in range(1, region_count + 1):
            if under_calibration[str(curr_ratios_update_index)]:
                current_ratios[str(curr_ratios_update_index)] = get_txtinout_ratios(txtinout_dir, curr_ratios_update_index, region_hrus, hru_areas)
                objective_ratios[str(curr_ratios_update_index)].precip = copy.deepcopy(current_ratios[str(curr_ratios_update_index)].precip)
                objective_ratios[str(curr_ratios_update_index)].get_values()

        # find differences in hydrological components           # later if satisfactory, drop region
        for hd_index in range(1, region_count + 1):
            if under_calibration[str(hd_index)]:
                history_differences[str(hd_index)].append(copy.deepcopy(get_difference(current_ratios[str(hd_index)], objective_ratios[str(hd_index)], current_parameters[str(hd_index)][par_index])))
                history_parameters[str(hd_index)].append(copy.deepcopy(current_parameters))

        # print difference history
        for tr_index in range(1, region_count + 1):
            try:
                tmp_trend = str(round(history_differences[str(tr_index)][0]), 3) if (not history_differences[str(tr_index)][0]) is None else "|"
            except:
                tmp_trend = "|"

            for tmp_item in history_differences[str(tr_index)]:
                if tmp_item == history_differences[str(tr_index)][0]:
                    continue
                tmp_trend += " -> " + str(round(tmp_item, 3))
            report(tmp_trend)

        # check history to calculate x_intercepts
        for xc_index in range(1, region_count + 1):
            if under_calibration[str(xc_index)]:
                pt_1 = point(history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value, history_differences[str(xc_index)][-2])
                pt_2 = point(history_parameters[str(xc_index)][-1][str(xc_index)][par_index].value, history_differences[str(xc_index)][-1])
                print("")
                report("adjustment informtion")
                print("\t    previous    parameter : {pp}, difference : {pd}".format(pp = str(round(pt_1.x, 3)).rjust(5), pd = str(round(pt_1.y, 3)).rjust(5)))
                print("\t    current     parameter : {cp}, difference : {cd}\n".format(cp = str(round(pt_2.x, 3)).rjust(5), cd = str(round(pt_2.y, 3)).rjust(5)))

                # check limits and bounds of next parameter
                probable_par = get_x_intercept(pt_1, pt_2)
                if not probable_par is None:
                    if probable_par > current_parameters[str(xc_index)][par_index].set_bound_u:
                        probable_par = current_parameters[str(xc_index)][par_index].set_bound_u
                    if probable_par < current_parameters[str(xc_index)][par_index].set_bound_l:
                        probable_par = current_parameters[str(xc_index)][par_index].set_bound_l

                if abs(pt_2.y) <= minimum_difference:
                    if pt_2.y > pt_1.y:
                        current_parameters[str(xc_index)][par_index].value = history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value
                        
                    report("{par_} has been set to {pv} for region {rgn}".format(
                        rgn     = xc_index,
                        pv      = current_parameters[str(xc_index)][par_index].value,
                        par_    = current_parameters[str(xc_index)][par_index].par_name
                    ))
                    under_calibration[str(xc_index)] = False
                    try:
                        if under_calibration[str(xc_index + 1)] == False:
                            under_calibration[str(xc_index + 1)] = True
                        sys.stdout.write("\t  - proceeding to region {rgn}".format(rgn = xc_index + 1))
                        # history_differences[str(xc_index + 1)].append(copy.deepcopy(get_difference(current_ratios[str(xc_index + 1)], objective_ratios[str(xc_index + 1)], current_parameters[str(xc_index + 1)][par_index])))
                    
                        break
                    except:
                        pass
                
                elif (history_differences[str(xc_index)][-1] == history_differences[str(xc_index)][-2]) and (len(history_differences[str(xc_index)]) > 2):
                    report("{par_} is no longer sensitive. it has been set to {pv} for region {rgn}".format(
                        rgn     = xc_index,
                        pv      = history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value,
                        par_    = current_parameters[str(xc_index)][par_index].par_name
                    ))
                    current_parameters[str(xc_index)][par_index].value = history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value
                    under_calibration[str(xc_index)] = False
                    try:
                        under_calibration[str(xc_index + 1)] = True
                        sys.stdout.write("\t  - proceeding to next region")
                        break
                    except:
                        pass


                elif probable_par is None:
                    report("{par_} is no longer sensitive. it has been set to {pv} for region {rgn}".format(
                        rgn     = xc_index,
                        pv      = history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value,
                        par_    = current_parameters[str(xc_index)][par_index].par_name
                    ))
                    current_parameters[str(xc_index)][par_index].value = history_parameters[str(xc_index)][-2][str(xc_index)][par_index].value
                    under_calibration[str(xc_index)] = False
                    try:
                        under_calibration[str(xc_index + 1)] = True
                        sys.stdout.write("\t  - proceeding to next region")
                        break
                    except:
                        pass
                elif probable_par == current_parameters[str(xc_index)][par_index].value:
                    report("suggested parameter value for {par_} is the same as the previous. it has been set to {pv} for region {rgn}".format(
                        rgn     = xc_index,
                        pv      = history_parameters[str(xc_index)][-1][str(xc_index)][par_index].value,
                        par_    = current_parameters[str(xc_index)][par_index].par_name
                    ))
                    current_parameters[str(xc_index)][par_index].value = history_parameters[str(xc_index)][-1][str(xc_index)][par_index].value
                    under_calibration[str(xc_index)] = False
                    try:
                        under_calibration[str(xc_index + 1)] = True
                        sys.stdout.write("\t  - proceeding to next region")
                        break
                    except:
                        pass
                else:
                    current_parameters[str(xc_index)][par_index].value = probable_par
                    report("trying parameter {par_v}".format(par_v = current_parameters[str(xc_index)][par_index].value))

        calibration_stop = True
        for ch_index in range(1, region_count + 1):
            if under_calibration[str(ch_index)] == True:
                calibration_stop = False
                break
        
        if calibration_stop:
            report("{par_n} has been calibrated in all regions".format(par_n = current_parameters[str(1)][par_index].par_name))
            break

for sc_str_index in range(1, region_count + 1):
    sc_string = sc_string.replace("sc_sr{z}".format(z = sc_str_index), "{sr_kw}")
    sc_string = sc_string.format(sr_kw = str(round(current_ratios[str(sc_str_index)].sr_r, 3)).rjust(13))
    sc_string = sc_string.replace("sc_et{z}".format(z = sc_str_index), "{et_kw}")
    sc_string = sc_string.format(et_kw = str(round(current_ratios[str(sc_str_index)].et_r, 3)).rjust(13))
    sc_string = sc_string.replace("sc_gw{z}".format(z = sc_str_index), "{gw_kw}")
    sc_string = sc_string.format(gw_kw = str(round(current_ratios[str(sc_str_index)].gw_r, 3)).rjust(13))

write_to("region_ratios_results.txt", sc_string)
report("soft calibration done", main = True, after = True)

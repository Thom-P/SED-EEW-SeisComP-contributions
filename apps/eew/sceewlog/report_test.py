# open pickle file and print report
# used to quickly test formatting without running playback

import pickle
import datetime

def generateReport():
        """
        Generate a report for an event, write it to disk and optionally send
        it as an email.
        """

        header_point_src, header_finite_src = createReportHeaders()

        # load pickle file
        pickle_file = '/home/sysop/.seiscomp/log/event_data.pkl'
        with open(pickle_file, 'rb') as f:
            ed_all = pickle.load(f)
        
        prefindex = sorted(ed_all['updates'].keys())[-1] # get the latest update as the preferred solution
        ed_pref = ed_all['updates'][prefindex]
        point_src_updates, finite_src_updates = [], []
        alert_index, update_index = -1, -1

        threshold_exceeded = False
        ed_all['diff'] = 9999
        for _i in sorted(ed_all['updates'].keys()):
            update_index += 1
            formatted_params_point_src, formatted_params_finite_fault = getFormattedUpdate(ed_all['updates'][_i], update_index, prefindex, ed_pref)
            point_src_updates.append("|".join(formatted_params_point_src))
            if formatted_params_finite_fault is not None:
                finite_src_updates.append("|".join(formatted_params_finite_fault))

        
        report_point_src = header_point_src + "\n".join(point_src_updates)
        report_finite_src = ""
        if len(finite_src_updates) > 0:
            report_finite_src = header_finite_src + "\n".join(finite_src_updates)

      
        report_pref = getFormattedPrefSolution(ed_pref)
        report = "\n\n".join([report_pref, report_point_src, report_finite_src])

        if True:
            ed_all['report'] = report
            f = open('test_report.txt', 'w')
            f.writelines(ed_all['report'])
            f.close()
        ed_all['type'] = ed['type']
        ed_all['magnitude'] = ed['magnitude']
        ed_all['published'] = True


def getFormattedPrefSolution(ed_pref):
    """
    Extract and format the preferred solution data for the report.
    """
    pref_params = (
            "EEW reference solution:\n",
            f"Time:   {ed_pref['ot'].replace('Z', ' UTC')}",
            f"Lat:    {ed_pref['lat']:.3f}",
            f"Lon:    {ed_pref['lon']:.3f}",
            f"Depth:  {ed_pref['depth']:.1f}",
            f"Mag:    {ed_pref['magnitude']:.2f} {ed_pref['type']}",
            f"Author: {ed_pref['author']}"
    )
    return "\n".join(pref_params)

def getFormattedUpdate(ed, update_index, prefindex, ed_pref):
    """
    Extract and format the update data for the report.
    """
    mag = ed['magnitude']
    threshold_exceeded = True

    #difftime = ed['tsobject'] - \
    #    ed_pref['tsobject']
    #ed['difftopref'] = difftime.length()
    # ed['difftopref'] += ed_pref['diff']

    simple_author = ed['author']
    author_split_index = simple_author.find("@")
    if author_split_index != -1:
        simple_author = simple_author[:author_split_index]
    ed['difftopref'] = 33.3333
    ed['diff'] = 36.6666

    #if ed['difftopref'] < ed_all['diff']:
    #    ed_all['diff'] = ed['difftopref']

    if ed['eew'] is True:
        alert_index += 1

    formatted_params_point_src = (
        f"{update_index:>3d}",
        f"{ed['difftopref']:>6.2f}",
        f"{ed['type']:>4s}",
        f"{mag:>5.2f}", 
        f"{ed['lat']:>7.3f}", 
        f"{ed['lon']:>8.3f}", 
        f"{ed['depth']:>6.1f}", 
        f"{ed['ot'][11:22]:>12s}", 
        f"{ed['likelihood']:5.2f}" if 'likelihood' in ed else "     ",
        f"{ed['nstorg']:>3d}",
        f"{ed['nstmag']:>3s}", 
        f" {ed['ts'][11:22]:s}", 
        f" {simple_author[:9]:<9s}", 
        f"{ed['diff']:>7.2f}",
        f"{alert_index:>4d}" if ed['eew'] else "    "
    )

    formatted_params_finite_fault = None
    if ed['centroid_lat'] is not None and ed['centroid_lon'] is not None:
        formatted_params_finite_fault = (
            f"{update_index:>3d}",
            f"{ed['difftopref']:6.2f}",
            f"{ed['centroid_lat']:7.3f}", 
            f"{ed['centroid_lon']:8.3f}", 
            f"{int(ed['rupture-strike']):4d}" if 'rupture-strike' in ed else "    ", 
            f"{ed['rupture-length']:5.1f}" if 'rupture-length' in ed else "     ", 
            f" {ed['ts'][11:22]:s}", 
            f" {simple_author[:9]:<9s}", 
        )
    return formatted_params_point_src, formatted_params_finite_fault


def createReportHeaders():
    """
    Create the headers for the report tables.
    """
    point_src = (
        "Table 1: Point-source solutions\n",
        "                                                                | #St.  |                               | Alert ",
        "  #|dt-ref|Type|  Mag|   Lat |    Lon | Depth|  Orig time | Lik | Or| Ma|   Creation | Author   |dt-curr| App",
        "---------------------------------------------------------------------------------------------------------------\n"
    )
    finite_source = (
        "Table 2: Finite-source solutions\n",
        "          |   Centroid     |                                                              ",
        "  #|dt-ref|   Lat |    Lon | Str| Len |   Creation | Author",
        "-----------------------------------------------------------\n"
    )
    return "\n".join(point_src), "\n".join(finite_source)


if __name__ == "__main__":
    generateReport()
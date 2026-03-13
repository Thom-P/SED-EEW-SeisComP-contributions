# open pickle file and print report
# used to quickly test formatting without running playback

import pickle

def generateReport():
        """
        Generate a report for an event, write it to disk and optionally send
        it as an email.
        """

        header_point_src, header_finite_src = createReportHeaders()

        pickle_file = './event_data.pkl'
        with open(pickle_file, 'rb') as f:
            ed_all = pickle.load(f)

        print(f"Alert counter: {ed_all['alert_counter']}")

        prefindex = sorted(ed_all['updates'].keys())[-1] # get the latest update as the preferred solution
        ed_pref = ed_all['updates'][prefindex]
        point_src_updates, finite_src_updates = [], []
        alert_index, update_index = -1, -1

        threshold_exceeded = False
        ed_all['diff'] = 9999
        for _i in sorted(ed_all['updates'].keys()):
            update_index += 1
            ed_curr = ed_all['updates'][_i]
            if ed_curr['eew'] is True:
                alert_index += 1
             
            #mag = ed['magnitude']
            threshold_exceeded = True

            #difftime = ed['tsobject'] - \
            #    ed_pref['tsobject']
            #ed['difftopref'] = difftime.length()
            # ed['difftopref'] += ed_pref['diff']
            
            #if ed['difftopref'] < ed_all['diff']:
            #    ed_all['diff'] = ed['difftopref']
            
            ed_curr['difftopref'] = 33.3333
            ed_curr['diff'] = 36.6666
            format_params_point_src, format_params_finite_src = getFormattedUpdate(ed_curr, update_index, alert_index)
            point_src_updates.append("|".join(format_params_point_src))
            if format_params_finite_src is not None:
                finite_src_updates.append("|".join(format_params_finite_src))
        
        report_point_src = header_point_src + "\n".join(point_src_updates)
        report_finite_src = ""
        if len(finite_src_updates) > 0:
            report_finite_src = header_finite_src + "\n".join(finite_src_updates)
      
        report_pref = getFormattedPrefSolution(ed_pref)
        report = "\n\n".join([report_pref, report_point_src, report_finite_src])

        if True:
            ed_all['report'] = report
            with open('test_report.txt', 'w') as f:
                f.writelines(ed_all['report'])
        ed_all['type'] = ed_pref['type']
        ed_all['magnitude'] = ed_pref['magnitude']
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

def getFormattedUpdate(ed, update_index, alert_index):
    """
    Extract and format individual update data for the report.
    """
    simple_author = ed['author']
    author_split_index = simple_author.find("@")
    if author_split_index != -1:
        simple_author = simple_author[:author_split_index]

    format_params_point_src = getFormatParamsPointSrc(ed, update_index, alert_index, simple_author)

    format_params_finite_src = None
    if ed['centroid_lat'] is not None and ed['centroid_lon'] is not None:
        format_params_finite_src = getFormatParamsFiniteSource(ed, update_index, simple_author)
    return format_params_point_src, format_params_finite_src

def getFormatParamsPointSrc(ed, update_index, alert_index, simple_author):
    """
    Extract and format the point-source solution data for the current update.
    """
    format_params_point_src = (
        f"{update_index:>3d}",
        f"{ed['difftopref']:>6.2f}",
        f"{ed['type']:>4s}",
        f"{ed['magnitude']:>5.2f}", 
        f"{ed['lat']:>7.3f}", 
        f"{ed['lon']:>8.3f}", 
        f"{ed['depth']:>6.1f}", 
        f"{ed['ot'][11:22]:>12s}", 
        f"{ed['likelihood']:5.2f}" if 'likelihood' in ed else " " * 5,
        f"{ed['nstorg']:>3d}",
        f"{ed['nstmag']:>3s}", 
        f" {ed['ts'][11:22]:s}", 
        f" {simple_author[:9]:<9s}", 
        f"{ed['diff']:>7.2f}",
        f"{alert_index:>4d}" if ed['eew'] else " " * 4
    )
    return format_params_point_src
           
def getFormatParamsFiniteSource(ed, update_index, simple_author):
    """
    Extract and format the finite-source solution data for the current update.
    """
    format_params_finite_src = (
        f"{update_index:>3d}",
        f"{ed['difftopref']:6.2f}",
        f"{ed['centroid_lat']:7.3f}", 
        f"{ed['centroid_lon']:8.3f}", 
        f"{int(ed['rupture-strike']):4d}" if 'rupture-strike' in ed else "    ", 
        f"{ed['rupture-length']:5.1f}" if 'rupture-length' in ed else "     ", 
        f" {ed['ts'][11:22]:s}", 
        f" {simple_author[:9]:<9s}",         
    )
    return format_params_finite_src

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
        "          |   Centroid     |",
        "  #|dt-ref|   Lat |    Lon | Str| Len |   Creation | Author",
        "-----------------------------------------------------------\n"
    )
    return "\n".join(point_src), "\n".join(finite_source)


if __name__ == "__main__":
    generateReport()
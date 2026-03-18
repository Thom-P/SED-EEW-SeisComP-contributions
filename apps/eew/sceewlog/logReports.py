# New report (centroid) generation functions for sceewlog

import os


def generateReport(event, report_headers):
    """
    Generate a report for an event, including the preferred solution, point-source and finite-source updates.
    Determine if the alert threshold is exceeded (done here to maintain legacy behavior).
    """

    header_point_src, header_finite_src = report_headers
    updates = sorted(event['updates'].keys())
    u_pref = updates[-1] # get the latest update as the preferred solution
    org_pref = event['updates'][u_pref]
    
    point_src_updates, finite_src_updates = getUpdatesSolutions(event, updates, org_pref)
    report_point_src = header_point_src + "\n".join(point_src_updates)
    report_finite_src = ""
    if len(finite_src_updates) > 0:
        report_finite_src = header_finite_src + "\n".join(finite_src_updates)

    report_pref = getFormattedPrefSolution(org_pref)
    report = "\n\n".join([report_pref, report_point_src, report_finite_src])
    
    event['diff'] = event['updates'][updates[0]]['difftopref'] # modified, first solution should be fastest by def
    event['type'] = org_pref['type']
    event['magnitude'] = org_pref['magnitude']
    event['report'] = report

def getUpdatesSolutions(event, updates, org_pref):
    """
    Build the point-source and finite-source solutions updates/lines for the report.
    """
    point_src_updates, finite_src_updates = [], []
    i_alert = -1

    #threshold_exceeded = False
    for i_update, update in enumerate(updates):
        org_curr = event['updates'][update]
        if org_curr['eew'] is True:
            i_alert += 1

        difftime = org_curr['tsobject'] - org_pref['tsobject']
        org_curr['difftopref'] = difftime.length() + org_pref['diff']
        
        format_params_point_src, format_params_finite_src = getFormattedUpdate(org_curr, i_update, i_alert)
        point_src_updates.append("|".join(format_params_point_src))
        if format_params_finite_src is not None:
            finite_src_updates.append("|".join(format_params_finite_src))
    return point_src_updates, finite_src_updates


def storeRep(evID, report_directory, report):
        """
        Store the generated report on disk.
        """
        if not os.path.isdir(report_directory):
            os.makedirs(report_directory)
        with open(os.path.join(report_directory,
                                f"{evID.replace('/', '_')}_report.txt"), 'w') as f:
            f.writelines(report)

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
        f"{int(ed['rupture-strike']):4d}" if 'rupture-strike' in ed else " " * 4, 
        f"{ed['rupture-length']:5.1f}" if 'rupture-length' in ed else " " * 5, 
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
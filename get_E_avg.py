import numpy as np
import h5py
import matplotlib.pyplot as plt

def collect_particles(filename, ptype):
    FILE = h5py.File(filename, 'r')
    pt_data = FILE["particles"]
    keys = pt_data.keys()
    if ptype not in keys:
        print("Particles %s was not found" % ptype)
        return np.array([])
    x = pt_data[ptype]['x'][:]
    y = pt_data[ptype]['y'][:]
    z = pt_data[ptype]['z'][:]
    Vx = pt_data[ptype]['Vx'][:]
    Vy = pt_data[ptype]['Vy'][:]
    Vz = pt_data[ptype]['Vz'][:]
    w = pt_data[ptype]['w'][:]
    data = np.column_stack((x, y, z, Vx, Vy, Vz, w))
    FILE.close()
    return data

def get_range_filter(column, rng):
    return (column>rng[0])*(column<rng[1])

def filter_particles(data, bnd_x, bnd_y, bnd_z):
    if len(data)==0:
        return data
    x_filter = get_range_filter(data[:,0], bnd_x)
    y_filter = get_range_filter(data[:,1], bnd_y)
    z_filter = get_range_filter(data[:,2], bnd_z)
    arr = data[x_filter*y_filter*z_filter]
    return arr

def mk_array_from_hist(hist, bins):
    arr = [[bins[0], hist[0]]]
    for i in range(1, len(bins)-1):
        arr.append([bins[i], hist[i-1]])
        arr.append([bins[i], hist[i]])
    arr.append([bins[-1], hist[-1]])
    return np.array(arr)


def convert_coor_ranges(dx, dy, dz):
    dx = dx.split(' ')
    dy = dy.split(' ')
    dz = dz.split(' ')
    for i in range(2):
        dx[i] = float(dx[i])
        dy[i] = float(dy[i])
        dz[i] = float(dz[i])
    return (dx, dy, dz)


def get_time(filename):
    FILE = h5py.File(filename, 'r')
    time = FILE.attrs['time']*1e9
    FILE.close()
    return time    #in ns


def convert_hist_to_points(bins_edges,hist):
    Y = np.zeros(2*len(hist))
    X = np.zeros(2*len(hist))    
    for i in range(len(hist)):
        Y[2 * i    ] = hist[i]
        Y[2 * i + 1] = hist[i]
        X[2 * i    ] = bins_edges[i]
        X[2 * i + 1] = bins_edges[i + 1]
    return np.column_stack((X, Y))

def get_average_energy(ptype, data):
    if len(data) == 0:
        return 0
    mass = {"e":9.1e-28, "H+":1.67e-24, "H2+":2*1.67e-24, "H3+":3*1.67e-24}
    energy = 0.5*mass[ptype]*(data[:,3]**2 + data[:,4]**2 + data[:,5]**2)*6.242e11    #in eV
    return sum(energy*data[:,-1])/data[:,-1].sum()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s'  ,'--species',action='store'     , default='H+ H2+ H3+' , help='list of particles I am interested in [def = "H+;H2+;H3+"]')
    parser.add_argument('-F' ,'--filter'  ,action='store_true', default=False        , help='True/False filter particle according to position or not [def = False]')
    parser.add_argument('-S' ,'--sum'     ,action='store_true', default=False        , help='True/False save summarized E_avg for all particles in list [def = False]')
    parser.add_argument('-dx' ,'--dx'     ,action='store'     , default='-7.0 7.0'   , help='x interval [def = "-7.0 7.0"]')
    parser.add_argument('-dy' ,'--dy'     ,action='store'     , default='8 9.5'      , help='y interval [def = "8 9.5"]')
    parser.add_argument('-dz' ,'--dz'     ,action='store'     , default='164.0 165.6', help='z interval [def = "164.0 165.6"]')
    parser.add_argument('-t' ,'--tag'     ,action='store'     , default=''           , help='tag for output file name [def = ""]')
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    
    
    pt_list = args.species.split(' ')
    tag = args.tag

    if args.filter:
        dx, dy, dz = convert_coor_ranges(args.dx, args.dy, args.dz)
        tag+="x_%s_y_%s_z_%s" % (args.dx, args.dy, args.dz)
        tag = tag.replace(' ', '_')
    
    E_avg = {}
    for ptype in pt_list:
        E_avg[ptype] = []
        
    for filename in args.files:
        print("PROCESSING FILE\t%s" % filename)
        time = get_time(filename)
        for ptype in pt_list:
            data = collect_particles(filename, ptype)
            if args.filter:
                data = filter_particles(data, dx, dy, dz)
            E_avg[ptype].append([time, get_average_energy(ptype, data)])
    
    if args.sum:
        summarized = []
        for i in range(len(E_avg[pt_list[0]])):
            time = E_avg[pt_list[0]][i][0]
            tmp = 0
            count = 0
            for k in E_avg.keys():
                tmp+=E_avg[k][i][1]
                count += 1 if E_avg[k][i][1]>0 else 0
            summarized.append([time, tmp/count])
        summarized = np.array(summarized)
        np.savetxt("E_avg_SUMMARIZED_" + tag + ".txt", summarized, delimiter='\t', fmt="%.6e", header="time, ns\tEnergy, eV")
    
    for k in E_avg.keys():
        np.savetxt("E_avg_%s_%s.txt" %(k, tag), np.array(E_avg[k]), delimiter='\t', fmt="%.6e", header="time, ns\tEnergy, eV")

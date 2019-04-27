import numpy as np
import sys
import os
import scipy
import pandas as pd
from scipy.interpolate import interp1d

from BigBadBrain.utils import timing

@timing
def load_fictrac(directory, file='fictrac.dat'):
    """ Loads fictrac data from .dat file that fictrac outputs.

    To-do: change units based on diameter of ball etc.
    For speed sanity check, instead remove bad frames so we don't have to throw out whole trial.

    Parameters
    ----------
    directory: string of full path to file
    file: string of file name

    Returns
    -------
    fictrac_data: pandas dataframe of all parameters saved by fictrac """

    with open(os.path.join(directory, file),'r') as f:
        df = pd.DataFrame(l.rstrip().split() for l in f)

        # Name columns
        df = df.rename(index=str, columns={0: 'frameCounter',
                                       1: 'dRotCamX',
                                       2: 'dRotCamY',
                                       3: 'dRotCamZ',
                                       4: 'dRotScore',
                                       5: 'dRotLabX',
                                       6: 'dRotLabY',
                                       7: 'dRotLabZ',
                                       8: 'AbsRotCamX',
                                       9: 'AbsRotCamY',
                                       10: 'AbsRotCamZ',
                                       11: 'AbsRotLabX',
                                       12: 'AbsRotLabY',
                                       13: 'AbsRotLabZ',
                                       14: 'positionX',
                                       15: 'positionY',
                                       16: 'heading',
                                       17: 'runningDir',
                                       18: 'speed',
                                       19: 'integratedX',
                                       20: 'integratedY',
                                       21: 'timeStamp',
                                       22: 'sequence'})

        # Remove commas
        for column in df.columns.values[:-1]:
            df[column] = [float(x[:-1]) for x in df[column]]

        fictrac_data = df
                
    # sanity check for extremely high speed (fictrac failure)
    speed = np.asarray(fictrac_data['speed'])
    max_speed = np.max(speed)
    if max_speed > 10:
        raise Exception('Fictrac ball tracking failed (reporting impossibly high speed).')
    return fictrac_data

@timing
def interpolate_fictrac(fictrac, timestamps, fps, dur, behavior='speed',sigma=3,sign=None):
    """ Interpolate fictrac.

    Parameters
    ----------
    fictrac: fictrac pandas dataframe.
    timestamps: [t,z] numpy array of imaging timestamps (to interpolate to).
    fps: camera frame rate (Hz)
    dur: int, duration of fictrac recording (in ms)
    behavior: column of dataframe to use
    sigma: for smoothing

    Returns
    -------
    fictrac_interp: [t,z] numpy array of fictrac interpolated to timestamps

    """
    camera_rate = 1/fps * 1000 # camera frame rate in ms
    raw_fictrac_times = np.arange(0,dur,camera_rate)
    
    # Cut off any extra frames (only happened with brain 4)
    fictrac = fictrac[:90000]
 
    if behavior == 'my_speed':
      dx = np.asarray(fictrac['dRotLabX'])
      dy = np.asarray(fictrac['dRotLabY'])
      dx = scipy.ndimage.filters.gaussian_filter(dx,sigma=3)
      dy = scipy.ndimage.filters.gaussian_filter(dy,sigma=3)
      fictrac_smoothed = np.sqrt(dx*dx + dy*dy)
    elif behavior == 'speed_all_3':
      dx = np.asarray(fictrac['dRotLabX'])
      dy = np.asarray(fictrac['dRotLabY'])
      dz = np.asarray(fictrac['dRotLabZ'])
      dx = scipy.ndimage.filters.gaussian_filter(dx,sigma=3)
      dy = scipy.ndimage.filters.gaussian_filter(dy,sigma=3)
      dz = scipy.ndimage.filters.gaussian_filter(dz,sigma=3)
      fictrac_smoothed = np.sqrt(dx*dx + dy*dy + dz*dz)
    else:
      fictrac_smoothed = scipy.ndimage.filters.gaussian_filter(np.asarray(fictrac[behavior]),sigma=sigma)

    if sign is not None and sign == 'abs':
      fictrac_smoothed = np.abs(fictrac_smoothed)
    elif sign is not None and sign == 'plus':
      fictrac_smoothed = np.clip(fictrac_smoothed,a_min=0,a_max=None)
    elif sign is not None and sign == 'minus':
      fictrac_smoothed = np.clip(fictrac_smoothed,a_min=None,a_max=0)
    elif sign is not None and sign == 'df':
      fictrac_smoothed = np.append(np.diff(fictrac_smoothed),0)
    elif sign is not None and sign == 'df_abs':
      fictrac_smoothed = np.abs(np.append(np.diff(fictrac_smoothed),0))

    # Interpolate
    # Warning: interp1d set to fill in out of bounds times
    fictrac_interp_temp = interp1d(raw_fictrac_times, fictrac_smoothed, bounds_error = False)
    fictrac_interp = fictrac_interp_temp(timestamps)
    
    # Replace Nans with zeros (for later code)
    np.nan_to_num(fictrac_interp, copy=False);
    
    return fictrac_interp

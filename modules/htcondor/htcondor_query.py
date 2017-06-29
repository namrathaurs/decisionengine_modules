#!/usr/bin/pyhon

import os
import sys
import abc

import htcondor


class QueryError(RuntimeError):
    """
    Thrown when there are exceptions using htcondor python bindings or commands
    """
    def __init__(self, err_str):
        RuntimeError.__init__(self, err_str)


class Query(object):
    """
    Pure virtual class to have a minimum set of methods defined
    """

    __metaclass__ = abc.ABCMeta


    def __init__(self):
        self.stored_data = {}


    def __repr__(self):
        return self.__str__()


    def __str__(self):
        return '%s' % vars(self)


    @abc.abstractmethod
    def fetch(self, constraint=None, format_list=None, condor_config=None):
        """
        Fetch the classad attributes specified in the format_list
        matching the constraint
        """
        return


    def load(self, constraint=None, format_list=None, condor_config=None):
        """
        Fetch the data and store it in self.stored_data
        """
        self.stored_data = self.fetch(constraint, format_list, condor_config)


    def fetch_stored(self, constraint_func=None):
        """
        :param constraint_func: A boolean function, with only one argument
                                (data el). If None, return all the data.
        :type constraint_func :obj: `Boolean function`

        @rtype: dict
        @return: Same as fetch(), but limited to constraint_func(el)==True
        """
        return apply_constraint(self.stored_data, constraint_func)


class CondorQuery(Query):
    """
    Fully implemented class for CondorQuery
    """

    def __init__(self, resource_str, group_attr, pool_name=None, env=None):
        if env is None:
            env = {}
        self.env = env
        self.resource_str = resource_str
        self.group_attr = group_attr
        self.pool_name = pool_name
        Query.__init__(self)


    #@abc.abstractmethod
    #def fetch(self, constraint=None, format_list=None):
    #    """
    #    Fetch the results using htcondor-python bindings
    #    """
    #    return


class CondorQ(CondorQuery):
    """
    Class to implement condor_q
    """

    def __init__(self, schedd_name=None, pool_name=None):
        self.schedd_name = schedd_name
        CondorQuery.__init__(self, 'schedd', ['ClusterId', 'ProcId'],
                             pool_name=pool_name)


    def fetch(self, constraint=None, format_list=None, condor_config=None):
        """
        Fetch job classads
        """

        results_dict = {}
        constraint = bindings_friendly_constraint(constraint)
        attrs = bindings_friendly_attrs(format_list)

        try:
            old_condor_config_env = os.environ.get('CONDOR_CONFIG')
            if condor_config and os.path.exists(condor_config):
                os.environ['CONDOR_CONFIG'] = condor_config
            htcondor.reload_config()
            if self.pool_name:
                collector = htcondor.Collector(str(self.pool_name))
            else:
                collector = htcondor.Collector()

            if self.schedd_name is None:
                schedd = htcondor.Schedd()
            else:
                schedd = htcondor.Schedd(
                    collector.locate(htcondor.DaemonTypes.Schedd,
                                     self.schedd_name))
            results = schedd.query(constraint, attrs)
            results_dict = list2dict(results, self.group_attr)
        except Exception as ex:
            s = 'default'
            if self.schedd_name is not None:
                s = self.schedd_name
            p = 'default'
            if self.pool_name is not None:
                p = self.pool_name
            err_str = 'Error querying schedd %s in pool %s using python bindings: %s' % (s, p, ex)
            raise QueryError(err_str), None, sys.exc_info()[2]
        finally:
            if old_condor_config_env:
                os.environ['CONDOR_CONFIG'] = old_condor_config_env

        return results_dict


class CondorStatus(CondorQuery):
    """
    Class to implement condor_status
    """

    def __init__(self, subsystem_name=None, pool_name=None, group_attr=None):
        if subsystem_name is None:
            subsystem_str = ''
        else:
            subsystem_str = '%s' % subsystem_name
        if group_attr is None:
            group_attr = ['Name']

        CondorQuery.__init__(self, subsystem_str, group_attr,
                             pool_name=pool_name)


    def fetch(self, constraint=None, format_list=None, condor_config=None):
        """
        Fetch resource classads and return a list of evaluated classads
        """

        results = []
        constraint = bindings_friendly_constraint(constraint)
        attrs = bindings_friendly_attrs(format_list)
        adtype = resource_str_to_py_adtype(self.resource_str)

        try:
            old_condor_config_env = os.environ.get('CONDOR_CONFIG')
            if condor_config and os.path.exists(condor_config):
                os.environ['CONDOR_CONFIG'] = condor_config
            htcondor.reload_config()
            if self.pool_name:
                collector = htcondor.Collector(str(self.pool_name))
            else:
                collector = htcondor.Collector()

            classads = collector.query(adtype, constraint, attrs)
            results = eval_classad_expr(classads)
        except Exception as ex:
            raise
            p = 'default'
            if self.pool_name is not None:
                p = self.pool_name
            err_str = 'Error querying pool %s using python bindings: %s' % (p, ex)
            raise QueryError(err_str), None, sys.exc_info()[2]
        finally:
            if old_condor_config_env:
                os.environ['CONDOR_CONFIG'] = old_condor_config_env

        return results


def apply_constraint(data, constraint_func):
    """
    Return a subset of data that satisfies constraint_function
    If constraint_func is None, return back entire data
    """

    if constraint_func is None:
        return data
    else:
        outdata = {}
        for key, val in data.iteritems():
            if constraint_func(val):
                outdata[key] = val
    return outdata


def resource_str_to_py_adtype(resource_str):
    """
    Given the resource string return equivalent classad type
    """

    adtypes = {
        'any': htcondor.AdTypes.Any,
        'collector': htcondor.AdTypes.Collector,
        'generic': htcondor.AdTypes.Generic,
        'grid': htcondor.AdTypes.Grid,
        'had': htcondor.AdTypes.HAD,
        'license': htcondor.AdTypes.License,
        'master': htcondor.AdTypes.Master,
        'negotiator': htcondor.AdTypes.Negotiator,
        'schedd': htcondor.AdTypes.Schedd,
        'startd': htcondor.AdTypes.Startd,
        'submitter': htcondor.AdTypes.Submitter
    }
    # Default to startd ads, even if resource_str is empty
    return adtypes.get(resource_str, htcondor.AdTypes.Startd)


def bindings_friendly_constraint(constraint):
    """
    Convert the constraint to format that can be used with python bindings
    """
    if constraint is None:
        return True
    return constraint


def bindings_friendly_attrs(format_list):
    """
    Convert the format_list into attrs that can be used with python bindings
    Python bindings should take care of the typing
    """
    attrs = []
    if format_list is not None:
        if isinstance(format_list, list):
            attrs = format_list
        elif isinstance(format_list, basestring):
            attrs = [format_list]
    return attrs


def list2dict(list_data, attr_name):
    """
    Convert a list to a dictionary and group the results based on
    attributes specified by attr_name
    """

    if isinstance(attr_name, (list, tuple)):
        attr_list = attr_name
    else:
        attr_list = [attr_name]

    dict_data = {}
    for list_el in list_data:
        if isinstance(attr_name, (list, tuple)):
            dict_name = []
            for an in attr_name:
                if an in list_el:
                    dict_name.append(list_el[an])
                else:
                    # Try lower cases
                    for k in list_el:
                        if an.lower()==k.lower():
                            dict_name.append(list_el[k])
                            break
            dict_name = tuple(dict_name)
        else:
            dict_name = list_el[attr_name]
        dict_el = {}
        for a in list_el:
            try:
                if (list_el[a].__class__.__name__ == 'ExprTree'):
                    # Try to evaluate the condor expr and use its value
                    # If cannot be evaluated, keep the expr as is
                    a_value = list_el[a].eval()
                    if '%s'%a_value != 'Undefined':
                        # Cannot use classad.Value.Undefined for
                        # for comparison as it gets cast to int
                        dict_el[a] = a_value
                elif str(list_el[a]) != 'Undefined':
                    # No need for Undefined check to see if
                    # attribute exists in the fetched classad
                    dict_el[a] = list_el[a]
            except:
                # Do not fail
                pass

        if dict_name not in dict_data:
            dict_data[dict_name] = []
        dict_data[dict_name].append(dict_el)
    return dict_data


def eval_classad_expr(classads):
    """
    Convert the classads into list of classads
    """

    classad_list = []
    for classad in classads:
        dict_el = {}
        for attr in classad:
            try:
                if (classad[attr].__class__.__name__ == 'ExprTree'):
                    a_value = classad[attr].eval()
                    if '%s'%a_value != 'Undefined':
                        # Cannot use classad.Value.Undefined
                        # for comparison as it gets cast to int
                        dict_el[attr] = a_value
                elif str(classad[attr]) != 'Undefined':
                    # No need for Undefined check to see if
                    # attribute exists in the fetched classad
                    dict_el[attr] = classad[attr]
            except:
                pass
        classad_list.append(dict_el)
    return classad_list

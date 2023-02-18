#!/usr/bin/env python
# -*- coding: utf-8 -*-

from data import *


class SrV2018:
    """ Maps SrV data to standard format"""

    @staticmethod
    def parking_position(x):

        if x == 1:
            return ParkingPosition.PRIVATE
        elif x == 2:
            return ParkingPosition.PUBLIC
        elif x == 3:
            return ParkingPosition.DIFFERENT

        return ParkingPosition.NA

    @staticmethod
    def economic_status(eink, persons):

        # Calculated according to Srv 2018
        # https://tu-dresden.de/bu/verkehr/ivs/srv/ressourcen/dateien/SrV2018_Tabellenbericht_Oberzentren_500TEW-_flach.pdf?lang=de

        if eink < 1:
            return EconomicStatus.UNKNOWN

        if eink == 1 or eink == 2:
            return EconomicStatus.VERY_LOW

        children = (persons.age < 14).sum()
        rest = len(persons) - children - 1

        w = 0.3 * children + 1 + 0.5 * rest

        if eink == 3:
            if w < 1.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 4:
            if w < 1.3:
                return EconomicStatus.MEDIUM
            elif w < 1.6:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 5:
            if w < 1.6:
                return EconomicStatus.MEDIUM
            elif w < 2.3:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 6:
            if w < 1.3:
                return EconomicStatus.HIGH
            elif w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.0:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 7:
            if w < 1.6:
                return EconomicStatus.HIGH
            elif w < 2.3:
                return EconomicStatus.MEDIUM
            elif w < 3.5:
                return EconomicStatus.LOW

            return EconomicStatus.VERY_LOW

        elif eink == 8:
            if w < 2.1:
                return EconomicStatus.HIGH
            elif w < 3.0:
                return EconomicStatus.MEDIUM

            return EconomicStatus.LOW

        elif eink == 9:
            if w < 1.3:
                return EconomicStatus.VERY_HIGH
            if w < 2.8:
                return EconomicStatus.HIGH
            return EconomicStatus.MEDIUM

        elif eink == 10:
            if w < 2.5:
                return EconomicStatus.VERY_HIGH

            return EconomicStatus.HIGH

        return EconomicStatus.UNKNOWN

    @staticmethod
    def household_type(x):
        if x == 1:
            return HouseholdType.MULTI_W_CHILDREN
        elif x == 2:
            return HouseholdType.MULTI_WO_CHILDREN

        return HouseholdType.SINGLE

    @staticmethod
    def gender(x):
        if x == 1:
            return Gender.M
        elif x == 2:
            return Gender.F

        return Gender.OTHER

    @staticmethod
    def employment(x):
        if x == 1:
            return Employment.CHILD
        elif x == 2:
            return Employment.HOMEMAKER
        elif x == 3:
            return Employment.RETIREE
        elif x == 5:
            return Employment.UNEMPLOYED
        elif x == 6:
            return Employment.SCHOOL
        elif x == 7:
            return Employment.STUDENT
        elif x == 8:
            return Employment.TRAINEE
        elif x == 9:
            return Employment.JOB_FULL_TIME
        elif x == 10 or x == 11:
            return Employment.JOB_PART_TIME

        return Employment.OTHER

    @staticmethod
    def yes_no(x):
        if x == 1:
            return Availability.YES
        elif x == 2:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def veh_avail(x):
        if x == 1 or x == 2:
            return Availability.YES
        elif x == 3:
            return Availability.NO

        return Availability.UNKNOWN

    @staticmethod
    def trip_mode(x):
        if x == 1:
            return TripMode.WALK
        if x == 2 or x == 18 or x == 19:
            return TripMode.BIKE
        if x == 4 or x == 5 or x == 6:
            return TripMode.CAR
        elif x == 7 or x == 8 or x == 9:
            return TripMode.RIDE
        elif 10 <= x <= 17:
            return TripMode.PT

        return TripMode.OTHER

    @staticmethod
    def trip_purpose(x):
        if x == 1:
            return Purpose.WORK
        elif x == 2:
            return Purpose.WORK_BUSINESS
        elif x == 3 or x == 4:
            return Purpose.EDU_PRIMARY
        elif x == 5 or x == 6:
            return Purpose.EDU_HIGHER
        elif x == 7:
            return Purpose.EDU_OTHER
        elif x == 8:
            return Purpose.SHOP_FOOD
        elif x == 9:
            return Purpose.SHOP_OTHER
        elif x == 19 or x == 10:
            return Purpose.PERSONAL_BUSINESS
        elif x == 11:
            return Purpose.TRANSPORT
        elif x == 15:
            return Purpose.OUTSIDE_RECREATION
        elif x == 13:
            return Purpose.DINING
        elif 12 <= x <= 17:
            return Purpose.LEISURE
        elif x == 18:
            return Purpose.HOME

        return Purpose.OTHER

    @staticmethod
    def sd_group(x):
        if x <= 0:
            return SourceDestinationGroup.UNKNOWN

        return list(SourceDestinationGroup)[int(x) - 1]

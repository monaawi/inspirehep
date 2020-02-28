import React, { useCallback, useMemo } from 'react';
import { DatePicker } from 'antd';
import moment from 'moment';

import withFormItem from '../withFormItem';

const BOTH_TRUE = [true, true];

function DateRangeField({ value = [], ...props }) {
  const { form, name } = props;

  const [startDate, endDate] = value;
  const valueAsMoment = useMemo(
    () => [startDate && moment(startDate), endDate && moment(endDate)],
    [startDate, endDate]
  );

  const onChange = useCallback(
    (_, range) => {
      form.setFieldValue(name, range);
    },
    [form, name]
  );

  const onBlur = useCallback(
    () => {
      form.setFieldTouched(name, true);
    },
    [form, name]
  );

  return (
    <DatePicker.RangePicker
      {...props}
      // set BOTH_TRUE for e2e, it is validate via schema any case.
      allowEmpty={BOTH_TRUE}
      data-test-type="date-range-picker"
      value={valueAsMoment}
      onBlur={onBlur}
      onChange={onChange}
      className="w-100"
    />
  );
}

export default withFormItem(DateRangeField);

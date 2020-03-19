import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Map } from 'immutable';
import { Link } from 'react-router-dom';

import './CitationSummaryTable.scss';
import ExternalLink from '../ExternalLink';
import LabelWithHelp from '../LabelWithHelp';
import LoadingOrChildren from '../LoadingOrChildren';
import ErrorAlertOrChildren from '../ErrorAlertOrChildren';
import { ErrorPropType } from '../../propTypes';
import FormattedNumber from '../FormattedNumber';

const PUBLISHED_HELP_MESSAGE = (
  <span>
    Published papers are believed to have undergone rigorous peer review.{' '}
    <ExternalLink href="http://inspirehep.net/info/faq/general#published">
      Learn More
    </ExternalLink>
  </span>
);

const H_INDEX_HELP_MESSAGE = (
  <span>
    The h-index is defined as the number of papers with citation number higher
    or equal to h. <Link to="/literature/690567">Learn more</Link>
  </span>
);

class CitationSummaryTable extends Component {
  render() {
    const {
      publishedBucket,
      citeableBucket,
      hIndex,
      loading,
      error,
      renderNumberOfCiteablePapers,
      renderNumberOfPublishedPapers,
    } = this.props;

    return (
      <LoadingOrChildren loading={loading}>
        <ErrorAlertOrChildren error={error}>
          <div className="__CitationTable__">
            <table>
              <tbody>
                <tr>
                  <th />
                  <th>
                    <LabelWithHelp
                      label="Citeable"
                      help="Citeable papers have metadata that allow us to reliably track their citations."
                    />
                  </th>
                  <th>
                    <LabelWithHelp
                      label="Published"
                      help={PUBLISHED_HELP_MESSAGE}
                    />
                  </th>
                </tr>
                <tr>
                  <th>Papers</th>
                  <td>
                    {renderNumberOfCiteablePapers(
                      citeableBucket.get('doc_count', 0)
                    )}
                  </td>
                  <td>
                    {renderNumberOfPublishedPapers(
                      publishedBucket.get('doc_count', 0)
                    )}
                  </td>
                </tr>
                <tr>
                  <th>Citations</th>
                  <td>
                    <FormattedNumber>
                      {citeableBucket.getIn(['citations_count', 'value'], 0)}
                    </FormattedNumber>
                  </td>
                  <td>
                    <FormattedNumber>
                      {publishedBucket.getIn(['citations_count', 'value'], 0)}
                    </FormattedNumber>
                  </td>
                </tr>
                <tr>
                  <th>
                    <LabelWithHelp
                      label="h-index"
                      help={H_INDEX_HELP_MESSAGE}
                    />
                  </th>
                  <td>{hIndex.get('all')}</td>
                  <td>{hIndex.get('published')}</td>
                </tr>
                <tr>
                  <th>Citations/paper (avg)</th>
                  <td>
                    <FormattedNumber>
                      {citeableBucket
                        .getIn(['average_citations', 'value'], 0)
                        .toFixed(1)}
                    </FormattedNumber>
                  </td>
                  <td>
                    <FormattedNumber>
                      {publishedBucket
                        .getIn(['average_citations', 'value'], 0)
                        .toFixed(1)}
                    </FormattedNumber>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </ErrorAlertOrChildren>
      </LoadingOrChildren>
    );
  }
}

CitationSummaryTable.propTypes = {
  publishedBucket: PropTypes.instanceOf(Map),
  citeableBucket: PropTypes.instanceOf(Map),
  hIndex: PropTypes.instanceOf(Map),
  renderNumberOfCiteablePapers: PropTypes.func,
  renderNumberOfPublishedPapers: PropTypes.func,
  loading: PropTypes.bool.isRequired,
  error: ErrorPropType,
};

CitationSummaryTable.defaultProps = {
  publishedBucket: Map(),
  citeableBucket: Map(),
  hIndex: Map(),
  renderNumberOfCiteablePapers: value => (
    <FormattedNumber>{value}</FormattedNumber>
  ),
  renderNumberOfPublishedPapers: value => (
    <FormattedNumber>{value}</FormattedNumber>
  ),
};

export default CitationSummaryTable;

/*
 * MIT License
 *
 * Copyright (c) 2020 Airbyte
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package io.airbyte.integrations.destination.jdbc;

import com.fasterxml.jackson.databind.JsonNode;
import io.airbyte.integrations.base.Destination;
import io.airbyte.integrations.base.ExtendedSQLNaming;
import io.airbyte.integrations.base.IntegrationRunner;
import org.jooq.SQLDialect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JdbcDestination extends AbstractJdbcDestination implements Destination {

  private static final Logger LOGGER = LoggerFactory.getLogger(JdbcDestination.class);

  public JdbcDestination() {
    super("org.postgresql.Driver", SQLDialect.POSTGRES, new ExtendedSQLNaming());
  }

  // no-op for JdbcIntegration since the config it receives is designed to be use for JDBC.
  @Override
  public JsonNode toJdbcConfig(JsonNode config) {
    return config;
  }

  @Override
  public String createTableQuery(String schemaName, String streamName) {
    return String.format(
        "CREATE TABLE IF NOT EXISTS %s.%s ( \n"
            + "ab_id VARCHAR PRIMARY KEY,\n"
            + "%s JSONB,\n"
            + "emitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n"
            + ");\n",
        schemaName, streamName, COLUMN_NAME);
  }

  public static void main(String[] args) throws Exception {
    final Destination destination = new JdbcDestination();
    LOGGER.info("starting destination: {}", JdbcDestination.class);
    new IntegrationRunner(destination).run(args);
    LOGGER.info("completed destination: {}", JdbcDestination.class);
  }

}
